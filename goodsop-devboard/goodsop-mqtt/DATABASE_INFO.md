# 数据库配置说明

## 数据库文件位置

### 开发环境
- **RK3562设备**: `D:/java/sqlite-tools-win-x64-3500300/rk3562.db`
- **RV1126设备**: `D:/java/sqlite-tools-win-x64-3500300/rv1126.db`

### 生产环境
- **Linux系统**: 建议配置为 `/opt/goodsop/data/{device_model}.db`
- **可通过环境变量**: `DATABASE_PATH` 来覆盖默认路径

## 数据库表结构

### device_info 表
设备信息表，存储设备的基本信息和绑定状态。

```sql
CREATE TABLE device_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id VARCHAR(255) UNIQUE NOT NULL,  -- 设备ID（CPU串号）
    device_model VARCHAR(50),                -- 设备型号（RK3562/RV1126）
    env VARCHAR(20),                         -- 环境标识（dev/prod）
    tenant_id VARCHAR(100),                  -- 租户ID
    user_id VARCHAR(100),                    -- 用户ID
    token VARCHAR(500),                      -- 认证令牌
    version_firmware VARCHAR(50),            -- 设备固件版本
    version_audio VARCHAR(50),               -- 音频固件版本
    is_bound BOOLEAN DEFAULT FALSE,          -- 是否已绑定
    created_at TIMESTAMP,                    -- 创建时间
    updated_at TIMESTAMP                     -- 更新时间
);
```

## 数据库操作

### 查看设备信息
```sql
SELECT * FROM device_info;
```

### 查看绑定状态
```sql
SELECT device_id, device_model, tenant_id, user_id, is_bound 
FROM device_info 
WHERE is_bound = 1;
```

### 查看认证状态
```sql
SELECT device_id, token, created_at, updated_at 
FROM device_info 
WHERE token IS NOT NULL;
```

## SQLite工具使用

### 连接数据库
```bash
# 进入SQLite工具目录
cd D:\java\sqlite-tools-win-x64-3500300

# 连接RK3562数据库
sqlite3.exe rk3562.db

# 连接RV1126数据库
sqlite3.exe rv1126.db
```

### 常用SQLite命令
```sql
-- 显示所有表
.tables

-- 显示表结构
.schema device_info

-- 设置列模式显示
.mode column
.headers on

-- 查询数据
SELECT * FROM device_info;

-- 退出
.quit
```

## 数据备份

### 备份命令
```bash
# 备份RK3562数据库
sqlite3.exe rk3562.db ".backup rk3562_backup_$(date +%Y%m%d).db"

# 备份RV1126数据库
sqlite3.exe rv1126.db ".backup rv1126_backup_$(date +%Y%m%d).db"
```

### 恢复命令
```bash
# 恢复数据库
sqlite3.exe rk3562.db ".restore rk3562_backup_20250724.db"
```

## 注意事项

1. **权限问题**: 确保应用有读写数据库文件的权限
2. **路径存在**: 确保数据库文件目录存在
3. **并发访问**: SQLite支持多读单写，注意并发控制
4. **文件锁定**: 避免多个应用同时写入同一数据库文件
5. **定期备份**: 建议定期备份重要数据

## 环境变量配置

可以通过以下环境变量覆盖默认配置：

```bash
# 数据库路径
export DATABASE_PATH=/custom/path/

# 完整的数据库URL
export SPRING_DATASOURCE_URL=jdbc:sqlite:/custom/path/device.db
```

## 监控和维护

### 数据库大小监控
```sql
-- 查看数据库文件大小
.dbinfo

-- 查看表记录数
SELECT COUNT(*) FROM device_info;
```

### 清理和优化
```sql
-- 清理过期数据（示例：清理30天前的未绑定设备）
DELETE FROM device_info 
WHERE is_bound = 0 
AND created_at < datetime('now', '-30 days');

-- 优化数据库
VACUUM;
```
