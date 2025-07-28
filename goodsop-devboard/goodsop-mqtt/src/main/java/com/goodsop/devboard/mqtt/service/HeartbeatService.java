package com.goodsop.devboard.mqtt.service;

import com.goodsop.devboard.mqtt.config.MqttProperties;
import com.goodsop.devboard.mqtt.model.DeviceStatusReport;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationContext;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

/**
 * 心跳服务
 */
@Slf4j
@Service
public class HeartbeatService {

    @Autowired
    private ApplicationContext applicationContext;

    @Autowired
    private DeviceService deviceService;

    @Autowired
    private MqttProperties mqttProperties;
    
    @Autowired
    private MqttService mqttService;
    
    /**
     * 获取MQTT服务实例（避免循环依赖）
     */
    private MqttService getMqttService() {
        return applicationContext.getBean(MqttService.class);
    }

    /**
     * 定时发送心跳
     * 每5分钟执行一次
     */
    @Scheduled(fixedRateString = "${mqtt.heartbeat-interval:5}", timeUnit = java.util.concurrent.TimeUnit.MINUTES)
    public void sendHeartbeat() {
        if (!mqttService.awaitConnection(10)) {
            log.warn("MQTT未连接，跳过此次心跳发送。");
            return;
        }

        try {
            log.info("正在发送心跳...");

            DeviceStatusReport statusReport = deviceService.createStatusReport("心跳");
            getMqttService().publishDeviceStatus(statusReport);

            log.debug("心跳发送成功");
        } catch (Exception e) {
            log.error("发送心跳失败", e);
        }
    }
    
    /**
     * 发送开机状态
     */
    public void sendStartupStatus() {
        try {
            log.info("正在发送开机状态...");

            DeviceStatusReport statusReport = deviceService.createStatusReport("开机");
            getMqttService().publishDeviceStatus(statusReport);

            log.info("开机状态发送成功");
        } catch (Exception e) {
            log.error("发送开机状态失败", e);
        }
    }

    /**
     * 发送关机状态
     */
    public void sendShutdownStatus() {
        try {
            log.info("正在发送关机状态...");

            DeviceStatusReport statusReport = deviceService.createStatusReport("关机");
            getMqttService().publishDeviceStatus(statusReport);

            log.info("关机状态发送成功");
        } catch (Exception e) {
            log.error("发送关机状态失败", e);
        }
    }

    /**
     * 发送绑定状态
     */
    public void sendBindingStatus() {
        try {
            log.info("正在发送绑定状态...");

            DeviceStatusReport statusReport = deviceService.createStatusReport("绑定");
            getMqttService().publishDeviceStatus(statusReport);

            log.info("绑定状态发送成功");
        } catch (Exception e) {
            log.error("发送绑定状态失败", e);
        }
    }

    /**
     * 发送解绑状态
     */
    public void sendUnbindingStatus() {
        try {
            log.info("正在发送解绑状态...");

            DeviceStatusReport statusReport = deviceService.createStatusReport("解绑");
            getMqttService().publishDeviceStatus(statusReport);

            log.info("解绑状态发送成功");
        } catch (Exception e) {
            log.error("发送解绑状态失败", e);
        }
    }
}
