package com.goodsop.devboard.mqtt.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

/**
 * 设备状态上报
 */
@Data
public class DeviceStatusReport {
    
    /**
     * 设备唯一标识ID
     */
    @JsonProperty("dId")
    private String deviceId;
    
    /**
     * 日志类型 (如 开机, 关机, 心跳, 绑定,解绑 等)
     */
    @JsonProperty("lt")
    private String logType;
    
    /**
     * 租户ID
     */
    @JsonProperty("tId")
    private String tenantId;
    
    /**
     * 用户ID
     */
    @JsonProperty("uId")
    private String userId;
    
    /**
     * 设备固件版本
     */
    @JsonProperty("vf")
    private String versionFirmware;
    
    /**
     * 音频固件版本
     */
    @JsonProperty("va")
    private String versionAudio;
    
    /**
     * 待上传文件数量
     */
    @JsonProperty("pufc")
    private Integer pendingUploadFilesCount;
    
    /**
     * 设备剩余存储空间 (单位:字节)
     */
    @JsonProperty("rsb")
    private Long remainingStorageBytes;
    
    /**
     * 设备电量百分比
     */
    @JsonProperty("blp")
    private Short batteryLevelPercent;
    
    /**
     * 设备信号强度 (单位:dBm)
     */
    @JsonProperty("ssd")
    private Short signalStrengthDbm;
    
    /**
     * 数据上报时间 (设备本地时间戳)
     */
    @JsonProperty("dt")
    private Long dataTime;
}
