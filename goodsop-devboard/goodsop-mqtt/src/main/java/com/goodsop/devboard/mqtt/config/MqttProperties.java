package com.goodsop.devboard.mqtt.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * MQTT配置属性
 */
@Data
@ConfigurationProperties(prefix = "mqtt")
public class MqttProperties {
    
    /**
     * MQTT服务器地址
     */
    private String serverUrl = "ssl://dev.goodsop.cn:8883";
    
    /**
     * 连接超时时间（秒）
     */
    private int connectionTimeout = 30;
    
    /**
     * 保持连接时间间隔（秒）
     */
    private int keepAliveInterval = 60;
    
    /**
     * 自动重连
     */
    private boolean automaticReconnect = true;
    
    /**
     * 清理会话
     */
    private boolean cleanSession = false;
    
    /**
     * 心跳间隔（分钟）
     */
    private int heartbeatInterval = 5;
    
    /**
     * 运行环境
     */
    private String env = "dev";
    
    /**
     * 设备型号
     */
    private String deviceModel = "RK3562";
}
