package com.goodsop.devboard.mqtt.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * MQTT配置类
 */
@Configuration
@EnableConfigurationProperties(MqttProperties.class)
@EnableScheduling
public class MqttConfig {
    
}
