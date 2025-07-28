# Goodsop MQTT 模块

这个模块实现了设备与MQTT服务器的通信功能，包括设备认证、状态上报、心跳机制等。

## 功能特性

- **自动连接**: 应用启动后自动建立MQTT连接
- **设备认证**: 使用CPU串号作为用户名，SHA256加密密码
- **消息订阅**: 自动订阅设备认证结果主题
- **状态上报**: 定时发送设备状态和心跳信息
- **数据持久化**: 保存设备信息、token、绑定信息到SQLite数据库
- **自动重连**: 连接断开时自动重连

## 配置说明

### MQTT配置

在 `application.yml` 中添加以下配置：

```yaml
mqtt:
  server-url: mqtts://dev.goodsop.cn:8883
  connection-timeout: 30
  keep-alive-interval: 60
  automatic-reconnect: true
  clean-session: false
  heartbeat-interval: 5
  device-model: RK3562
```

### 数据库配置

```yaml
spring:
  datasource:
    # 开发环境：数据库文件保存在SQLite工具目录
    url: jdbc:sqlite:D:/java/sqlite-tools-win-x64-3500300/rk3562.db
    driver-class-name: org.sqlite.JDBC
  jpa:
    hibernate:
      ddl-auto: update
```

## 使用方法

### 1. 添加依赖

在你的项目 `pom.xml` 中添加：

```xml
<dependency>
    <groupId>com.goodsop.devboard</groupId>
    <artifactId>goodsop-mqtt</artifactId>
    <version>1.0.0-SNAPSHOT</version>
</dependency>
```

### 2. 启用组件扫描

在你的主应用类上添加包扫描：

```java
@SpringBootApplication(scanBasePackages = "com.goodsop.devboard")
public class YourApplication {
    public static void main(String[] args) {
        SpringApplication.run(YourApplication.class, args);
    }
}
```

### 3. 配置文件

将 `application-mqtt.yml` 的内容合并到你的配置文件中。

## 主要组件

### MqttService
- 负责MQTT连接管理
- 处理消息订阅和发布
- 处理设备认证、绑定、解绑消息
- 使用Lombok简化代码，中文日志输出

### DeviceService
- 管理设备信息
- 创建设备状态报告
- 更新设备认证和绑定信息
- 使用Lombok @Slf4j注解

### HeartbeatService
- 定时发送心跳（默认5分钟）
- 发送开机、关机、绑定、解绑状态
- 中文日志记录所有操作

### DeviceUtils
- 获取设备ID（CPU串号）
- 检测设备型号
- 跨平台支持（Windows/Linux）
- 使用Lombok简化日志

### CryptoUtils
- 生成MQTT连接密码
- SHA256加密
- 生成客户端ID

## 消息格式

### 订阅主题
```
{env}/{deviceModel}/{deviceId}/base/result
```

### 发布主题
```
{env}/{deviceModel}/{deviceId}/{tenantId}/{userId}/base/status
```

### 状态上报格式
```json
{
  "dId": "设备ID",
  "lt": "心跳",
  "tId": "租户ID",
  "uId": "用户ID",
  "vf": "1.0.0",
  "va": "0.0.1",
  "pufc": 10,
  "rsb": 800,
  "blp": 55,
  "ssd": -97,
  "dt": 1751619085
}
```

## API文档

### Knife4j访问地址
- **RK3562设备**: http://localhost:28803/doc.html
- **RV1126设备**: http://localhost:28802/doc.html

### 统一返回值
所有Controller接口都使用统一的Result返回格式：

```java
@GetMapping("/device-info")
public Result<Map<String, Object>> getDeviceInfo() {
    try {
        // 业务逻辑
        return Result.success("获取设备信息成功", data);
    } catch (Exception e) {
        return Result.error("获取设备信息失败: " + e.getMessage());
    }
}
```

## 测试

运行测试：

```bash
mvn test
```

## 注意事项

1. 确保设备能够访问MQTT服务器地址
2. 设备需要有唯一的CPU串号或MAC地址
3. **数据库文件位置**:
   - 开发环境：`D:/java/sqlite-tools-win-x64-3500300/{device_model}.db`
   - 生产环境：可通过配置文件指定路径
4. 心跳间隔可以通过配置调整
5. 支持SSL/TLS连接（mqtts://）
6. **日志输出**: 所有日志均为中文描述，便于调试
7. **Lombok支持**: 使用Lombok简化代码，需要IDE安装Lombok插件

## 故障排除

### 连接失败
- 检查网络连接
- 验证MQTT服务器地址和端口
- 检查防火墙设置

### 认证失败
- 确认设备ID获取正确
- 检查密码生成逻辑
- 验证时间同步

### 消息发送失败
- 确认设备已绑定（有tenantId和userId）
- 检查主题格式
- 验证消息格式
