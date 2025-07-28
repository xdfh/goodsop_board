[MQTT需求]
1.项目启动后就开始建立连接，
地址：mqtts://dev.goodsop.cn:8883
用户名(username)：获取本机CPU串号（注意开发环境是win11，生产是linux）
密码(password)：SHA256(username+YYYYMMDDHHmm)

变量说明：
env = spring.profiles.active
deviceModel = RK3562/RV1126,我们使用哪一个启动就是哪一个
deviceId = 本机CPU串号

tenantId =
userId =

tenantId / userId 是设备绑定后下发的，等待下发后保存到数据库使用
clientId = {deviceId}_{YYYYMM}，每月过期，代表翻月就丢弃离线缓存的消息


设备认证：
参数:    
{
"password": "",
"username": ""
}
username=deviceId
连接成功订阅：（这里会下发设备认证成功后的一些数据）
{env}/{deviceModel}/{deviceId}/base/result

备注：有两类消息
1.主要获取token使用（一般连接成功后10秒内下发）
响应数据：
```angular2html
{
  "code": 1,
  "msg": "认证结果",
  "time": "2025-07-22 15:48:16.188",
  "timestamp": "1753170496188",
  "data": {
    "deviceId": "FFFFFFFF",
    "result": "allow",
    "token": "003c8906-f713-44c2-b11c-82e0ee871114_FFFFFFFF",
    "time": "2025-07-22 15:48:16.186",
    "timestamp": "1753170496186"
  }
}
```
2.主要获取 tenantId / userId 保存使用（未知下发时间）
```angular2html
{
  "code": 2,
  "msg": "设备绑定通知",
  "time": "2025-07-24 16:15:14.788",
  "timestamp": "1753344914788",
  "data": {
    "tenantId": "T100",
    "deviceModel": "A10",
    "env": "dev",
    "deviceId": "A10",
    "userId": "U100"
  }
}

{
"code": 3,
"msg": "设备解绑通知",
"time": "2025-07-24 16:20:07.273",
"timestamp": "1753345207273",
"data": null
}
```

设备状态上报格式：（每5分钟向服务器发送一次心跳）
{env}/{deviceModel}/{deviceId}/{tenantId}/{userId}/base/status
```angular2html
Topic: dev/A10/FFFFFFFF/T100/U100/base/statusQoS: 1

{

  "dId": "FFFFFFFF",
  "lt": "心跳",
  "tId": "T100",
  "uId": "U10",
  "vf": "1.0.0",
  "va": "0.0.1",
  "pufc": 10,
  "rsb": 800,
  "blp": 55,
  "ssd": -97,
  "dt": 1751619085
}
```

```
服务端接收和字段定义代码，用来参考的
@Schema(description = "设备唯一标识ID")
@JsonProperty("dId")
private String deviceId;

@Schema(description = "日志类型 (如 开机, 关机, 心跳, 绑定,解绑 等)")
@JsonProperty("lt")
private String logType;

@Schema(description = "设备固件版本")
@JsonProperty("vf")
private String versionFirmware;

@Schema(description = "音频固件版本")
@JsonProperty("va")
private String versionAudio;

@Schema(description = "待上传文件数量")
@JsonProperty("pufc")
private Integer pendingUploadFilesCount;

@Schema(description = "设备剩余存储空间 (单位:字节)")
@JsonProperty("rsb")
private Long remainingStorageBytes;

@Schema(description = "设备电量百分比")
@JsonProperty("blp")
private Short batteryLevelPercent;

@Schema(description = "设备信号强度 (单位:dBm)")
@JsonProperty("ssd")
private Short signalStrengthDbm;

@Schema(description = "数据上报时间 (设备本地时间戳)")
@JsonProperty("dt")
private Long dataTime;
```

