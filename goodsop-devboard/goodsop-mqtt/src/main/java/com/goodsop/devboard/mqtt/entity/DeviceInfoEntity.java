package com.goodsop.devboard.mqtt.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

/**
 * 设备信息实体
 */
@Data
@TableName("device_info")
public class DeviceInfoEntity {

    @TableId(type = IdType.AUTO)
    private Long id;
    
    /**
     * 设备ID（CPU串号）
     */
    @TableField("device_id")
    private String deviceId;

    /**
     * 设备型号
     */
    @TableField("device_model")
    private String deviceModel;

    /**
     * 环境标识
     */
    @TableField("env")
    private String env;

    /**
     * 租户ID
     */
    @TableField("tenant_id")
    private String tenantId;

    /**
     * 用户ID
     */
    @TableField("user_id")
    private String userId;

    /**
     * 认证令牌
     */
    @TableField("token")
    private String token;

    /**
     * 设备固件版本
     */
    @TableField("version_firmware")
    private String versionFirmware = "1.0.0";

    /**
     * 音频固件版本
     */
    @TableField("version_audio")
    private String versionAudio = "0.0.1";

    /**
     * 是否已绑定
     */
    @TableField("is_bound")
    private Boolean isBound = false;

    /**
     * 创建时间
     */
    @TableField("created_at")
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    @TableField("updated_at")
    private LocalDateTime updatedAt;
}
