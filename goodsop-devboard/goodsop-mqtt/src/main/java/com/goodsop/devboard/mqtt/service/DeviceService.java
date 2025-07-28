package com.goodsop.devboard.mqtt.service;

import com.goodsop.devboard.mqtt.entity.DeviceInfoEntity;
import com.goodsop.devboard.mqtt.model.DeviceStatusReport;
import com.goodsop.devboard.mqtt.repository.DeviceInfoRepository;
import com.goodsop.devboard.mqtt.util.DeviceUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.File;
import java.time.Instant;
import java.time.LocalDateTime;

/**
 * 设备服务
 */
@Slf4j
@Service
public class DeviceService {
    
    @Autowired
    private DeviceInfoRepository deviceInfoRepository;
    
    @Value("${spring.profiles.active:dev}")
    private String activeProfile;
    
    /**
     * 获取或创建设备信息
     * 
     * @return 设备信息
     */
    public DeviceInfoEntity getOrCreateDeviceInfo() {
        String deviceId = DeviceUtils.getDeviceId();
        String deviceModel = DeviceUtils.detectDeviceModel();

        DeviceInfoEntity existingDevice = deviceInfoRepository.findByDeviceId(deviceId);

        if (existingDevice != null) {
            // 更新设备型号和环境信息
            existingDevice.setDeviceModel(deviceModel);
            existingDevice.setEnv(activeProfile);
            existingDevice.setUpdatedAt(LocalDateTime.now());
            deviceInfoRepository.updateById(existingDevice);
            return existingDevice;
        } else {
            // 创建新的设备信息
            DeviceInfoEntity newDevice = new DeviceInfoEntity();
            newDevice.setDeviceId(deviceId);
            newDevice.setDeviceModel(deviceModel);
            newDevice.setEnv(activeProfile);
            newDevice.setCreatedAt(LocalDateTime.now());
            newDevice.setUpdatedAt(LocalDateTime.now());
            deviceInfoRepository.insert(newDevice);
            return newDevice;
        }
    }
    
    /**
     * 更新设备认证信息
     * 
     * @param deviceId 设备ID
     * @param token 认证令牌
     */
    public void updateDeviceAuth(String deviceId, String token) {
        DeviceInfoEntity device = deviceInfoRepository.findByDeviceId(deviceId);
        if (device != null) {
            device.setToken(token);
            device.setUpdatedAt(LocalDateTime.now());
            deviceInfoRepository.updateById(device);
            log.info("已更新设备认证信息，设备ID: {}", deviceId);
        } else {
            log.warn("设备认证更新失败，未找到设备: {}", deviceId);
        }
    }
    
    /**
     * 更新设备绑定信息
     * 
     * @param deviceId 设备ID
     * @param tenantId 租户ID
     * @param userId 用户ID
     */
    public void updateDeviceBinding(String deviceId, String tenantId, String userId) {
        DeviceInfoEntity device = deviceInfoRepository.findByDeviceId(deviceId);
        if (device != null) {
            device.setTenantId(tenantId);
            device.setUserId(userId);
            device.setIsBound(true);
            device.setUpdatedAt(LocalDateTime.now());
            deviceInfoRepository.updateById(device);
            log.info("已更新设备绑定信息，设备ID: {}, 租户ID: {}, 用户ID: {}",
                       deviceId, tenantId, userId);
        } else {
            log.warn("设备绑定更新失败，未找到设备: {}", deviceId);
        }
    }
    
    /**
     * 解绑设备
     * 
     * @param deviceId 设备ID
     */
    public void unbindDevice(String deviceId) {
        DeviceInfoEntity device = deviceInfoRepository.findByDeviceId(deviceId);
        if (device != null) {
            device.setTenantId(null);
            device.setUserId(null);
            device.setIsBound(false);
            device.setUpdatedAt(LocalDateTime.now());
            deviceInfoRepository.updateById(device);
            log.info("已解绑设备: {}", deviceId);
        } else {
            log.warn("设备解绑失败，未找到设备: {}", deviceId);
        }
    }
    
    /**
     * 创建设备状态报告
     * 
     * @param logType 日志类型
     * @return 设备状态报告
     */
    public DeviceStatusReport createStatusReport(String logType) {
        DeviceInfoEntity device = getOrCreateDeviceInfo();
        
        DeviceStatusReport report = new DeviceStatusReport();
        report.setDeviceId(device.getDeviceId());
        report.setLogType(logType);
        report.setTenantId(device.getTenantId());
        report.setUserId(device.getUserId());
        report.setVersionFirmware(device.getVersionFirmware());
        report.setVersionAudio(device.getVersionAudio());
        report.setDataTime(Instant.now().getEpochSecond());
        
        // 设置系统状态信息
        report.setPendingUploadFilesCount(getPendingUploadFilesCount());
        report.setRemainingStorageBytes(getRemainingStorageBytes());
        report.setBatteryLevelPercent(getBatteryLevelPercent());
        report.setSignalStrengthDbm(getSignalStrengthDbm());
        
        return report;
    }
    
    /**
     * 获取待上传文件数量
     * 
     * @return 待上传文件数量
     */
    private Integer getPendingUploadFilesCount() {
        // TODO: 实现获取待上传文件数量的逻辑
        return 0;
    }
    
    /**
     * 获取剩余存储空间
     * 
     * @return 剩余存储空间（字节）
     */
    private Long getRemainingStorageBytes() {
        try {
            File root = new File("/");
            return root.getFreeSpace();
        } catch (Exception e) {
            log.debug("获取剩余存储空间失败", e);
            return 0L;
        }
    }
    
    /**
     * 获取电量百分比
     * 
     * @return 电量百分比
     */
    private Short getBatteryLevelPercent() {
        // TODO: 实现获取电量的逻辑
        return 100;
    }
    
    /**
     * 获取信号强度
     * 
     * @return 信号强度（dBm）
     */
    private Short getSignalStrengthDbm() {
        // TODO: 实现获取信号强度的逻辑
        return -50;
    }
}
