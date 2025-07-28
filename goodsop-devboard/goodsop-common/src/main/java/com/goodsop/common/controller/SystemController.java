package com.goodsop.common.controller;

import com.goodsop.common.core.enums.ResultCode;
import com.goodsop.common.core.model.Result;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * 系统信息控制器
 */
@RestController
@RequestMapping("/api/system")
public class SystemController {

    /**
     * 系统健康检查
     */
    @GetMapping("/health")
    public Result<Map<String, Object>> health() {
        Map<String, Object> data = new HashMap<>();
        data.put("status", "UP");
        data.put("timestamp", LocalDateTime.now());
        data.put("version", "1.0.0");
        
        return Result.success("系统运行正常", data);
    }

    /**
     * 获取系统信息
     */
    @GetMapping("/info")
    public Result<Map<String, Object>> info() {
        Map<String, Object> data = new HashMap<>();
        data.put("applicationName", "Goodsop设备板系统");
        data.put("version", "1.0.0");
        data.put("javaVersion", System.getProperty("java.version"));
        data.put("osName", System.getProperty("os.name"));
        data.put("osVersion", System.getProperty("os.version"));
        data.put("startTime", LocalDateTime.now());
        
        return Result.success("获取系统信息成功", data);
    }

    /**
     * 测试错误返回
     */
    @GetMapping("/error-test")
    public Result<Void> errorTest() {
        return Result.error(ResultCode.INTERNAL_SERVER_ERROR.getCode(), 
                           "这是一个测试错误消息");
    }

    /**
     * 测试自定义状态码
     */
    @GetMapping("/mqtt-error-test")
    public Result<Void> mqttErrorTest() {
        return Result.error(ResultCode.MQTT_CONNECT_ERROR.getCode(), 
                           ResultCode.MQTT_CONNECT_ERROR.getMessage());
    }
}
