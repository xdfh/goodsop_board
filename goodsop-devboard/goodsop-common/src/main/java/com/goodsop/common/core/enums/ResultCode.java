package com.goodsop.common.core.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 返回状态码枚举
 */
@Getter
@AllArgsConstructor
public enum ResultCode {

    /**
     * 成功
     */
    SUCCESS(200, "操作成功"),

    /**
     * 失败
     */
    ERROR(500, "操作失败"),

    /**
     * 参数错误
     */
    PARAM_ERROR(400, "参数错误"),

    /**
     * 未授权
     */
    UNAUTHORIZED(401, "未授权"),

    /**
     * 禁止访问
     */
    FORBIDDEN(403, "禁止访问"),

    /**
     * 资源不存在
     */
    NOT_FOUND(404, "资源不存在"),

    /**
     * 请求方法不支持
     */
    METHOD_NOT_ALLOWED(405, "请求方法不支持"),

    /**
     * 系统内部错误
     */
    INTERNAL_SERVER_ERROR(500, "系统内部错误"),

    /**
     * 服务不可用
     */
    SERVICE_UNAVAILABLE(503, "服务不可用"),

    // MQTT相关状态码
    /**
     * MQTT连接失败
     */
    MQTT_CONNECT_ERROR(1001, "MQTT连接失败"),

    /**
     * 设备未绑定
     */
    DEVICE_NOT_BOUND(1002, "设备未绑定"),

    /**
     * 设备认证失败
     */
    DEVICE_AUTH_ERROR(1003, "设备认证失败"),

    /**
     * 消息发送失败
     */
    MESSAGE_SEND_ERROR(1004, "消息发送失败"),

    /**
     * 设备离线
     */
    DEVICE_OFFLINE(1005, "设备离线");

    /**
     * 状态码
     */
    private final int code;

    /**
     * 消息
     */
    private final String message;
}
