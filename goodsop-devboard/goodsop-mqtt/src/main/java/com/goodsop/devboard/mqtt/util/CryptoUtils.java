package com.goodsop.devboard.mqtt.util;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * 加密工具类
 */
public class CryptoUtils {
    
    private static final DateTimeFormatter PASSWORD_TIME_FORMAT = DateTimeFormatter.ofPattern("yyyyMMddHHmm");
    
    /**
     * 生成MQTT连接密码
     * 密码格式：SHA256(username+YYYYMMDDHHmm)
     * 
     * @param username 用户名（设备ID）
     * @return 加密后的密码
     */
    public static String generateMqttPassword(String username) {
        String timeStr = LocalDateTime.now().format(PASSWORD_TIME_FORMAT);
        String plainText = username + timeStr;
        return sha256(plainText);
    }
    
    /**
     * SHA256加密
     * 
     * @param input 输入字符串
     * @return SHA256加密后的十六进制字符串
     */
    public static String sha256(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(input.getBytes(StandardCharsets.UTF_8));
            
            StringBuilder hexString = new StringBuilder();
            for (byte b : hash) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) {
                    hexString.append('0');
                }
                hexString.append(hex);
            }
            
            return hexString.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("SHA-256 algorithm not available", e);
        }
    }
    
    /**
     * 生成客户端ID
     * 格式：{deviceId}_{YYYYMM}
     * 
     * @param deviceId 设备ID
     * @return 客户端ID
     */
    public static String generateClientId(String deviceId) {
        String monthStr = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMM"));
        return deviceId + "_" + monthStr;
    }
}
