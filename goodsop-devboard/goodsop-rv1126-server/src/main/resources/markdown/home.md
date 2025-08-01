# Goodsop RV1126设备API文档

## 系统简介

欢迎使用Goodsop RV1126设备管理系统API文档。本系统提供了完整的设备管理、MQTT通信、文件处理等功能。

## 主要功能模块

### 🔌 MQTT通信模块
- **设备认证**: 自动获取CPU序列号进行设备认证
- **消息订阅**: 订阅设备认证结果和绑定通知
- **状态上报**: 定时发送设备心跳和状态信息
- **实时通信**: 支持SSL/TLS安全连接

### 📱 设备管理模块
- **设备信息**: 管理设备基本信息和绑定状态
- **状态监控**: 实时监控设备运行状态
- **配置管理**: 动态配置设备参数

### 📁 文件处理模块
- **文件上传**: 支持多种格式文件上传
- **文件下载**: 提供文件下载服务
- **存储管理**: 管理设备存储空间

### 🌐 网络通信模块
- **网络配置**: 管理设备网络连接
- **通信协议**: 支持多种通信协议
- **连接监控**: 监控网络连接状态

## 技术架构

- **框架**: Spring Boot 3.2.5
- **数据库**: SQLite
- **消息队列**: MQTT (Eclipse Paho)
- **文档工具**: Knife4j + OpenAPI 3
- **代码简化**: Lombok
- **日志框架**: Slf4j

## 快速开始

### 1. 环境要求
- JDK 17+
- Maven 3.6+
- SQLite 3.x

### 2. 启动应用
```bash
mvn spring-boot:run
```

### 3. 访问文档
- API文档地址: http://localhost:28802/doc.html
- 应用端口: 28802

## 接口说明

### 统一返回格式
所有接口均使用统一的返回格式：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {},
  "timestamp": 1640995200000
}
```

### 状态码说明
- `200`: 操作成功
- `400`: 参数错误
- `401`: 未授权
- `403`: 禁止访问
- `404`: 资源不存在
- `500`: 系统内部错误
- `1001`: MQTT连接失败
- `1002`: 设备未绑定
- `1003`: 设备认证失败

## 注意事项

1. **数据库文件**: 位于 `D:/java/sqlite-tools-win-x64-3500300/rv1126.db`
2. **日志输出**: 所有日志均为中文描述
3. **MQTT连接**: 自动连接到 `mqtts://dev.goodsop.cn:8883`
4. **心跳间隔**: 默认5分钟发送一次心跳
5. **设备型号**: 当前设备型号为 RV1126

## 联系我们

- 开发团队: Goodsop开发团队
- 邮箱: dev@goodsop.cn
- 官网: https://www.goodsop.cn

---

*本文档由Knife4j自动生成，最后更新时间: 2025-07-24*
