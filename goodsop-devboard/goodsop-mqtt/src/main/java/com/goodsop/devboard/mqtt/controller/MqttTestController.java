package com.goodsop.devboard.mqtt.controller;

import com.goodsop.common.core.model.Result;
import com.goodsop.devboard.mqtt.entity.DeviceInfoEntity;
import com.goodsop.devboard.mqtt.model.DeviceStatusReport;
import com.goodsop.devboard.mqtt.service.DeviceService;
import com.goodsop.devboard.mqtt.service.HeartbeatService;
import com.goodsop.devboard.mqtt.service.MqttService;
import com.goodsop.devboard.mqtt.util.DeviceUtils;
// import io.swagger.annotations.Api;
// import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

/**
 * MQTT测试控制器
 */
@RestController
@RequestMapping("/api/mqtt")
public class MqttTestController {
    
    @Autowired
    private DeviceService deviceService;
    
    @Autowired
    private HeartbeatService heartbeatService;
    
    @Autowired
    private MqttService mqttService;
    
    /**
     * 获取设备信息
     */
    @GetMapping("/device-info")
    public Result<Map<String, Object>> getDeviceInfo() {
        try {
            Map<String, Object> data = new HashMap<>();

            String deviceId = DeviceUtils.getDeviceId();
            String deviceModel = DeviceUtils.detectDeviceModel();
            DeviceInfoEntity deviceInfo = deviceService.getOrCreateDeviceInfo();

            data.put("deviceId", deviceId);
            data.put("deviceModel", deviceModel);
            data.put("deviceInfo", deviceInfo);

            return Result.success("获取设备信息成功", data);
        } catch (Exception e) {
            return Result.error("获取设备信息失败: " + e.getMessage());
        }
    }
    
    /**
     * 手动发送心跳
     */
    @PostMapping("/send-heartbeat")
    public Result sendHeartbeat() {
        try {
            heartbeatService.sendHeartbeat();
            return Result.success("心跳发送成功");
        } catch (Exception e) {
            return Result.error("心跳发送失败: " + e.getMessage());
        }
    }
    
    /**
     * 发送测试状态
     */
    @PostMapping("/send-test-status")
    public Result<DeviceStatusReport> sendTestStatus() {
        try {
            DeviceStatusReport statusReport = deviceService.createStatusReport("测试");
            mqttService.publishDeviceStatus(statusReport);
            return Result.success("测试状态发送成功", statusReport);
        } catch (Exception e) {
            return Result.error("测试状态发送失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取MQTT连接状态
     */
    @GetMapping("/connection-status")
    public Result<Map<String, Object>> getConnectionStatus() {
        try {
            Map<String, Object> data = new HashMap<>();

            // 这里可以添加获取MQTT连接状态的逻辑
            data.put("connected", true); // 简化实现
            data.put("serverUrl", "mqtts://dev.goodsop.cn:8883");
            data.put("lastConnectTime", System.currentTimeMillis());

            return Result.success("获取连接状态成功", data);
        } catch (Exception e) {
            return Result.error("获取连接状态失败: " + e.getMessage());
        }
    }
}
