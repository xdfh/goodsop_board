# API开发使用说明

## 统一返回值Result使用指南

### 1. 基本使用

#### 成功返回
```java
// 简单成功返回
return Result.success();

// 返回数据
return Result.success(data);

// 自定义成功消息
return Result.success("操作成功", data);
```

#### 失败返回
```java
// 简单失败返回
return Result.error();

// 自定义错误消息
return Result.error("操作失败");

// 自定义状态码和消息
return Result.error(400, "参数错误");

// 使用枚举状态码
return Result.error(ResultCode.PARAM_ERROR.getCode(), 
                   ResultCode.PARAM_ERROR.getMessage());
```

### 2. 控制器示例

```java
@Tag(name = "用户管理", description = "用户相关接口")
@RestController
@RequestMapping("/api/user")
public class UserController {

    @Operation(summary = "获取用户信息", description = "根据用户ID获取用户详细信息")
    @GetMapping("/{id}")
    public Result<User> getUserById(@PathVariable Long id) {
        try {
            User user = userService.findById(id);
            if (user == null) {
                return Result.error(ResultCode.NOT_FOUND.getCode(), "用户不存在");
            }
            return Result.success("获取用户信息成功", user);
        } catch (Exception e) {
            log.error("获取用户信息失败", e);
            return Result.error("获取用户信息失败: " + e.getMessage());
        }
    }

    @Operation(summary = "创建用户", description = "创建新用户")
    @PostMapping
    public Result<User> createUser(@RequestBody @Valid UserCreateRequest request) {
        try {
            User user = userService.create(request);
            return Result.success("用户创建成功", user);
        } catch (Exception e) {
            log.error("用户创建失败", e);
            return Result.error("用户创建失败: " + e.getMessage());
        }
    }
}
```

### 3. 状态码使用

#### 系统预定义状态码
- `200`: 操作成功
- `400`: 参数错误
- `401`: 未授权
- `403`: 禁止访问
- `404`: 资源不存在
- `500`: 系统内部错误

#### MQTT相关状态码
- `1001`: MQTT连接失败
- `1002`: 设备未绑定
- `1003`: 设备认证失败
- `1004`: 消息发送失败
- `1005`: 设备离线

#### 自定义状态码
```java
// 在ResultCode枚举中添加新的状态码
USER_NOT_FOUND(2001, "用户不存在"),
USER_ALREADY_EXISTS(2002, "用户已存在"),
PASSWORD_ERROR(2003, "密码错误");
```

## Knife4j使用指南

### 1. 访问地址
- **RK3562设备**: http://localhost:28803/doc.html
- **RV1126设备**: http://localhost:28802/doc.html

### 2. 注解使用

#### 控制器注解
```java
@Tag(name = "接口分组名称", description = "接口分组描述")
@RestController
@RequestMapping("/api/xxx")
public class XxxController {
    // ...
}
```

#### 方法注解
```java
@Operation(summary = "接口简要说明", description = "接口详细描述")
@GetMapping("/xxx")
public Result<Xxx> getXxx() {
    // ...
}
```

#### 参数注解
```java
@Operation(summary = "根据ID查询")
@GetMapping("/{id}")
public Result<User> getById(
    @Parameter(description = "用户ID", required = true) 
    @PathVariable Long id) {
    // ...
}

@Operation(summary = "分页查询")
@GetMapping
public Result<Page<User>> getPage(
    @Parameter(description = "页码", example = "1") 
    @RequestParam(defaultValue = "1") Integer page,
    @Parameter(description = "每页大小", example = "10") 
    @RequestParam(defaultValue = "10") Integer size) {
    // ...
}
```

#### 请求体注解
```java
@Operation(summary = "创建用户")
@PostMapping
public Result<User> create(
    @io.swagger.v3.oas.annotations.parameters.RequestBody(
        description = "用户创建请求", 
        required = true
    )
    @RequestBody @Valid UserCreateRequest request) {
    // ...
}
```

### 3. 模型注解

```java
@Schema(description = "用户信息")
@Data
public class User {
    
    @Schema(description = "用户ID", example = "1")
    private Long id;
    
    @Schema(description = "用户名", example = "admin")
    private String username;
    
    @Schema(description = "邮箱", example = "admin@example.com")
    private String email;
    
    @Schema(description = "创建时间")
    private LocalDateTime createTime;
}
```

### 4. 配置说明

```yaml
knife4j:
  enable: true                    # 启用Knife4j
  setting:
    language: zh_cn               # 中文界面
    enable-version: true          # 显示版本
    enable-swagger-models: true   # 显示模型
    enable-document-manage: true  # 文档管理
    swagger-model-name: 实体类列表 # 模型列表名称
    enable-host-text: API文档     # 主机显示文本
    enable-home-custom: true      # 自定义首页
    home-custom-location: classpath:markdown/home.md  # 首页文档位置
```

## 最佳实践

### 1. 异常处理
```java
@RestController
public class XxxController {
    
    @GetMapping("/xxx")
    public Result<Xxx> getXxx() {
        try {
            // 业务逻辑
            Xxx data = xxxService.getXxx();
            return Result.success("获取成功", data);
        } catch (BusinessException e) {
            // 业务异常
            log.warn("业务异常: {}", e.getMessage());
            return Result.error(e.getCode(), e.getMessage());
        } catch (Exception e) {
            // 系统异常
            log.error("系统异常", e);
            return Result.error("系统异常，请稍后重试");
        }
    }
}
```

### 2. 参数验证
```java
@PostMapping
public Result<User> create(@RequestBody @Valid UserCreateRequest request) {
    // Spring Validation会自动验证参数
    // 验证失败会抛出MethodArgumentNotValidException
    // 可以通过全局异常处理器统一处理
    return Result.success("创建成功", userService.create(request));
}
```

### 3. 分页查询
```java
@GetMapping
public Result<Page<User>> getPage(
    @RequestParam(defaultValue = "1") Integer page,
    @RequestParam(defaultValue = "10") Integer size) {
    
    Page<User> pageData = userService.getPage(page, size);
    return Result.success("查询成功", pageData);
}
```

### 4. 文件上传
```java
@PostMapping("/upload")
public Result<String> upload(@RequestParam("file") MultipartFile file) {
    try {
        String url = fileService.upload(file);
        return Result.success("上传成功", url);
    } catch (Exception e) {
        log.error("文件上传失败", e);
        return Result.error("文件上传失败: " + e.getMessage());
    }
}
```

## 注意事项

1. **统一返回格式**: 所有Controller接口都必须使用Result作为返回值
2. **中文消息**: 所有返回消息都使用中文描述
3. **异常处理**: 必须捕获异常并返回友好的错误信息
4. **日志记录**: 重要操作和异常都要记录日志
5. **参数验证**: 使用@Valid注解进行参数验证
6. **API文档**: 使用Swagger注解完善API文档
