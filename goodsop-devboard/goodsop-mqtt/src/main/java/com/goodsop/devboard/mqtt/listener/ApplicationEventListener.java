package com.goodsop.devboard.mqtt.listener;

import com.goodsop.devboard.mqtt.service.HeartbeatService;
import com.goodsop.devboard.mqtt.service.MqttService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.ContextClosedEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

/**
 * 应用事件监听器
 */
@Slf4j
@Component
public class ApplicationEventListener {
    
    @Autowired
    private HeartbeatService heartbeatService;
    
    @Autowired
    private MqttService mqttService;

    /**
     * 应用准备就绪后，发送开机状态
     */
    @EventListener(ApplicationReadyEvent.class)
    public void handleApplicationReady() {
        new Thread(() -> {
            log.info("应用启动完成，等待MQTT连接...");
            boolean connected = mqttService.awaitConnection(60); // 等待最多60秒
            if (connected) {
                log.info("MQTT连接成功，准备发送开机状态...");
                heartbeatService.sendStartupStatus();
            } else {
                log.error("MQTT连接超时，无法发送开机状态。");
            }
        }).start();
    }

    /**
     * 应用关闭事件
     */
    @EventListener
    public void handleContextClosed(ContextClosedEvent event) {
        log.info("应用正在关闭，发送关机状态...");
        heartbeatService.sendShutdownStatus();
    }
}
