package com.goodsop.devboard.mqtt.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

/**
 * 设备绑定通知
 */
@Data
public class DeviceBindingNotification {
    
    @JsonProperty("code")
    private Integer code;
    
    @JsonProperty("msg")
    private String msg;
    
    @JsonProperty("time")
    private String time;
    
    @JsonProperty("timestamp")
    private String timestamp;
    
    @JsonProperty("data")
    private BindingData data;

    @Data
    public static class BindingData {
        @JsonProperty("tenantId")
        private String tenantId;
        
        @JsonProperty("deviceModel")
        private String deviceModel;
        
        @JsonProperty("env")
        private String env;
        
        @JsonProperty("deviceId")
        private String deviceId;
        
        @JsonProperty("userId")
        private String userId;
    }
}
