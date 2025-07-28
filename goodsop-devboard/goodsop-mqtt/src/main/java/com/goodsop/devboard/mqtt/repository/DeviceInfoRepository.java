package com.goodsop.devboard.mqtt.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.goodsop.devboard.mqtt.entity.DeviceInfoEntity;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

/**
 * 设备信息 Mapper
 */
@Mapper
public interface DeviceInfoRepository extends BaseMapper<DeviceInfoEntity> {

    /**
     * 根据设备ID查找设备信息
     *
     * @param deviceId 设备ID
     * @return 设备信息
     */
    @Select("SELECT * FROM device_info WHERE device_id = #{deviceId}")
    DeviceInfoEntity findByDeviceId(String deviceId);

    /**
     * 检查设备ID是否存在
     *
     * @param deviceId 设备ID
     * @return 是否存在
     */
    @Select("SELECT COUNT(1) FROM device_info WHERE device_id = #{deviceId}")
    boolean existsByDeviceId(String deviceId);
}
