package com.goodsop.devboard.mqtt.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.goodsop.devboard.mqtt.config.MqttProperties;
import com.goodsop.devboard.mqtt.entity.DeviceInfoEntity;
import com.goodsop.devboard.mqtt.model.DeviceAuthResponse;
import com.goodsop.devboard.mqtt.model.DeviceBindingNotification;
import com.goodsop.devboard.mqtt.model.DeviceStatusReport;
import com.goodsop.devboard.mqtt.util.CryptoUtils;
import com.goodsop.devboard.mqtt.util.DeviceUtils;
import lombok.extern.slf4j.Slf4j;
import org.eclipse.paho.client.mqttv3.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Service;

import javax.annotation.PreDestroy;
import javax.net.ssl.SSLSocketFactory;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

import org.springframework.context.ApplicationContext;

/**
 * MQTT服务
 */
@Slf4j
@Service
public class MqttService implements MqttCallback {

    @Autowired
    private MqttProperties mqttProperties;

    @Autowired
    private DeviceService deviceService;

    private MqttClient mqttClient;
    private ObjectMapper objectMapper = new ObjectMapper();
    private String deviceId;
    private final CountDownLatch connectionLatch = new CountDownLatch(1);

    @Autowired
    private ApplicationContext applicationContext;

    /**
     * 应用启动后初始化MQTT连接
     */
    @EventListener(ApplicationReadyEvent.class)
    public void initializeMqtt() {
        try {
            deviceId = DeviceUtils.getDeviceId();
            
            log.info("正在初始化MQTT连接，设备ID: {}, 设备型号: {}, 环境: {}", 
                deviceId, mqttProperties.getDeviceModel(), mqttProperties.getEnv());

            connectToMqtt();
        } catch (Exception e) {
            log.error("初始化MQTT连接失败", e);
        }
    }

    /**
     * 连接到MQTT服务器
     */
    private void connectToMqtt() throws MqttException {
        String clientId = CryptoUtils.generateClientId(deviceId);

        mqttClient = new MqttClient(mqttProperties.getServerUrl(), clientId, null);
        mqttClient.setCallback(this);

        MqttConnectOptions options = new MqttConnectOptions();
        options.setUserName(deviceId);
        options.setPassword(CryptoUtils.generateMqttPassword(deviceId).toCharArray());
        options.setConnectionTimeout(mqttProperties.getConnectionTimeout());
        options.setKeepAliveInterval(mqttProperties.getKeepAliveInterval());
        options.setAutomaticReconnect(mqttProperties.isAutomaticReconnect());
        options.setCleanSession(mqttProperties.isCleanSession());

        // 解决MQTTS连接问题，Paho使用 ssl:// 协议
        if (mqttProperties.getServerUrl().startsWith("ssl")) {
            try {
                options.setSocketFactory(SSLSocketFactory.getDefault());
            } catch (Exception e) {
                log.error("无法设置SSLSocketFactory", e);
                // 可以选择抛出异常或进行其他错误处理
                throw new MqttException(e);
            }
        }

        try {
            log.info("正在连接MQTT服务器: {}", mqttProperties.getServerUrl());
            mqttClient.connect(options);
            // 连接成功后订阅认证结果主题
            subscribeToAuthResult();
        } catch (MqttException e) {
            log.error("连接MQTT服务器失败", e);
            throw e; // 将异常重新抛出，以便上层可以捕获
        }
    }

    /**
     * 订阅设备认证结果主题
     */
    private void subscribeToAuthResult() throws MqttException {
        String topic = String.format("%s/%s/%s/base/result", 
            mqttProperties.getEnv(), mqttProperties.getDeviceModel(), deviceId);

        // 对于同步客户端，subscribe是阻塞方法，成功则继续，失败则抛出异常
        mqttClient.subscribe(topic, 1);

        log.info("已订阅主题: {}", topic);
        connectionLatch.countDown(); // 订阅成功后，释放锁
        log.info("MQTT客户端已准备就绪。");
    }

    /**
     * 等待MQTT连接成功
     * @param timeoutSeconds 等待超时时间（秒）
     * @return 是否在超时时间内连接成功
     */
    public boolean awaitConnection(long timeoutSeconds) {
        try {
            return connectionLatch.await(timeoutSeconds, TimeUnit.SECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.warn("等待MQTT连接时被中断", e);
            return false;
        }
    }

    /**
     * 发布设备状态
     *
     * @param statusReport 状态报告
     */
    public void publishDeviceStatus(DeviceStatusReport statusReport) {
        if (mqttClient == null || !mqttClient.isConnected()) {
            log.warn("MQTT客户端未连接，无法发布状态");
            return;
        }

        DeviceInfoEntity deviceInfo = deviceService.getOrCreateDeviceInfo();
        if (deviceInfo.getTenantId() == null || deviceInfo.getUserId() == null) {
            log.warn("设备未绑定，无法发布状态");
            return;
        }

        try {
            String topic = String.format("%s/%s/%s/%s/%s/base/status", 
                                       mqttProperties.getEnv(), mqttProperties.getDeviceModel(), deviceId, 
                                       deviceInfo.getTenantId(), deviceInfo.getUserId());
            
            String payload = objectMapper.writeValueAsString(statusReport);

            MqttMessage message = new MqttMessage(payload.getBytes());
            message.setQos(1);

            mqttClient.publish(topic, message);
            log.debug("已发布状态到主题: {}", topic);
        } catch (Exception e) {
            log.error("发布设备状态失败", e);
        }
    }

    @Override
    public void connectionLost(Throwable cause) {
        log.warn("MQTT连接丢失", cause);
        // 自动重连由MqttConnectOptions.setAutomaticReconnect(true)处理
    }

    @Override
    public void messageArrived(String topic, MqttMessage message) throws Exception {
        String payload = new String(message.getPayload());
        log.info("收到消息，主题: {}, 内容: {}", topic, payload);

        try {
            // 预解析以获取code
            com.fasterxml.jackson.databind.JsonNode rootNode = objectMapper.readTree(payload);
            int code = rootNode.path("code").asInt();

            switch (code) {
                case 1: // 认证结果
                    DeviceAuthResponse authResponse = objectMapper.treeToValue(rootNode, DeviceAuthResponse.class);
                    handleAuthResult(authResponse);
                    break;
                case 2: // 设备绑定通知
                    DeviceBindingNotification bindingNotification = objectMapper.treeToValue(rootNode, DeviceBindingNotification.class);
                    handleDeviceBinding(bindingNotification);
                    break;
                case 3: // 设备解绑通知
                    handleDeviceUnbinding();
                    break;
                default:
                    log.warn("收到未知的消息代码: {}", code);
            }
        } catch (Exception e) {
            log.error("处理接收到的消息失败", e);
        }
    }

    @Override
    public void deliveryComplete(IMqttDeliveryToken token) {
        log.debug("消息发送完成: {}", token.getMessageId());
    }

    /**
     * 处理认证结果
     *
     * @param authResponse 认证响应
     */
    private void handleAuthResult(DeviceAuthResponse authResponse) {
        if (authResponse.getData() != null && "allow".equals(authResponse.getData().getResult())) {
            String token = authResponse.getData().getToken();
            deviceService.updateDeviceAuth(deviceId, token);
            log.info("设备认证成功，已接收到token");
        } else {
            log.warn("设备认证失败");
        }
    }

    /**
     * 处理设备绑定
     *
     * @param bindingNotification 绑定通知
     */
    private void handleDeviceBinding(DeviceBindingNotification bindingNotification) {
        if (bindingNotification.getData() != null) {
            DeviceBindingNotification.BindingData data = bindingNotification.getData();
            // 强制使用客户端自己的deviceId，忽略payload中的deviceId
            deviceService.updateDeviceBinding(this.deviceId, data.getTenantId(), data.getUserId());
            log.info("设备已绑定到租户: {}, 用户: {}", data.getTenantId(), data.getUserId());

            // 发送绑定状态
            try {
                HeartbeatService heartbeatService = applicationContext.getBean(HeartbeatService.class);
                heartbeatService.sendBindingStatus();
            } catch (Exception e) {
                log.warn("发送绑定状态失败", e);
            }
        }
    }

    /**
     * 处理设备解绑
     */
    private void handleDeviceUnbinding() {
        deviceService.unbindDevice(deviceId);
        log.info("设备已解绑");

        // 发送解绑状态
        try {
            HeartbeatService heartbeatService = applicationContext.getBean(HeartbeatService.class);
            heartbeatService.sendUnbindingStatus();
        } catch (Exception e) {
            log.warn("发送解绑状态失败", e);
        }
    }

    /**
     * 应用关闭时断开MQTT连接
     */
    @PreDestroy
    public void disconnect() {
        if (mqttClient != null && mqttClient.isConnected()) {
            try {
                mqttClient.disconnect();
                mqttClient.close();
                log.info("MQTT客户端已断开连接");
            } catch (MqttException e) {
                log.error("断开MQTT客户端连接时出错", e);
            }
        }
    }
}
