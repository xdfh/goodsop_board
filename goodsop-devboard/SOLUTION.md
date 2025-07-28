# Spring Boot 启动错误解决方案

## 问题描述
应用启动时出现错误：
```
java.lang.IllegalArgumentException: Invalid value type for attribute 'factoryBeanObjectType': java.lang.String
```

## 根本原因
这个错误通常由以下原因引起：
1. Spring Integration 自动配置冲突
2. MyBatis-Plus 与 Spring Boot 3.x 版本兼容性问题
3. 配置属性类的注解使用不当

## 解决方案

### 1. 已修复的问题

#### A. 移除了 Spring Integration 依赖
- 从 `goodsop-mqtt/pom.xml` 中移除了 `spring-integration-mqtt`
- 保留 Eclipse Paho MQTT 客户端，功能不受影响

#### B. 修复了配置属性类
- 移除了 `MqttProperties` 类中的 `@Component` 注解
- 保留 `@ConfigurationProperties` 和 `@EnableConfigurationProperties`

#### C. 添加了全面的自动配置排除
- 在主应用类和配置文件中排除了问题自动配置

### 2. 当前配置状态

#### 主应用类配置：
```java
@SpringBootApplication(
    scanBasePackages = "com.goodsop.devboard",
    exclude = {
        org.springframework.boot.autoconfigure.integration.IntegrationAutoConfiguration.class,
        org.springframework.boot.autoconfigure.jms.JmsAutoConfiguration.class,
        org.springframework.boot.autoconfigure.jms.activemq.ActiveMQAutoConfiguration.class,
        com.baomidou.mybatisplus.autoconfigure.MybatisPlusAutoConfiguration.class
    }
)
@MapperScan("com.goodsop.devboard.**.repository")
```

#### 配置文件排除：
```yaml
spring:
  autoconfigure:
    exclude:
      - org.springframework.boot.autoconfigure.integration.IntegrationAutoConfiguration
      - org.springframework.boot.autoconfigure.jms.JmsAutoConfiguration
      - org.springframework.boot.autoconfigure.jms.activemq.ActiveMQAutoConfiguration
      - com.baomidou.mybatisplus.autoconfigure.MybatisPlusAutoConfiguration
```

### 3. 如果问题仍然存在

#### 选项 A：降级 MyBatis-Plus 版本
在父 pom.xml 中修改版本：
```xml
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-boot-starter</artifactId>
    <version>3.5.3.1</version>
</dependency>
```

#### 选项 B：使用 Spring Data JPA 替代 MyBatis-Plus
1. 移除 MyBatis-Plus 依赖
2. 添加 Spring Data JPA：
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>
```

#### 选项 C：完全禁用数据库自动配置（临时测试）
```yaml
spring:
  autoconfigure:
    exclude:
      - org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration
      - org.springframework.boot.autoconfigure.orm.jpa.HibernateJpaAutoConfiguration
```

### 4. 验证步骤

1. 清理项目：`mvn clean`
2. 重新编译：`mvn compile`
3. 启动应用：`mvn spring-boot:run -pl goodsop-rk3562-server`

### 5. 预期结果

应用应该能够正常启动，看到类似日志：
```
INFO --- [main] c.g.d.rk3562.Rk3562ServerApplication : Starting Rk3562ServerApplication
INFO --- [main] c.g.d.rk3562.Rk3562ServerApplication : The following 1 profile is active: "dev"
INFO --- [main] o.s.b.w.embedded.tomcat.TomcatWebServer : Tomcat started on port(s): 28803 (http)
INFO --- [main] c.g.d.rk3562.Rk3562ServerApplication : Started Rk3562ServerApplication
```

### 6. 功能验证

启动成功后，验证以下功能：
- Web 服务器在端口 28803 启动
- MQTT 服务正常初始化
- 数据库连接正常（如果启用）

## 注意事项

1. 当前配置临时禁用了 MyBatis-Plus，如需数据库功能，请选择上述选项之一
2. MQTT 功能完全保留，使用 Eclipse Paho 客户端
3. 所有其他模块功能不受影响
