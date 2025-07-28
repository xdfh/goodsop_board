package com.goodsop.devboard.mqtt.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

/**
 * 设备认证响应
 */
@Data
public class DeviceAuthResponse {
    
    @JsonProperty("code")
    private Integer code;
    
    @JsonProperty("msg")
    private String msg;
    
    @JsonProperty("time")
    private String time;
    
    @JsonProperty("timestamp")
    private String timestamp;
    
    @JsonProperty("data")
    private AuthData data;

    @Data
    public static class AuthData {
        @JsonProperty("deviceId")
        private String deviceId;
        
        @JsonProperty("result")
        private String result;
        
        @JsonProperty("token")
        private String token;
        
        @JsonProperty("time")
        private String time;
        
        @JsonProperty("timestamp")
        private String timestamp;
    }
}
