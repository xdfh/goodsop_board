-- For SQLite
CREATE TABLE IF NOT EXISTS device_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id VARCHAR(255) NOT NULL UNIQUE,
    device_model VARCHAR(50),
    env VARCHAR(50),
    tenant_id VARCHAR(100),
    user_id VARCHAR(100),
    token TEXT,
    version_firmware VARCHAR(50) DEFAULT '1.0.0',
    version_audio VARCHAR(50) DEFAULT '0.0.1',
    is_bound BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
); 