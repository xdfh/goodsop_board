# -*- coding: utf-8 -*-


import os
import logging
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Any, Dict

# 1. 这是我们的自定义设置加载器。
def py_file_settings_source(settings_cls: type[BaseSettings]) -> dict[str, Any]:
    """
    一个从 .py 文件加载变量的设置源。
    """
    config = {}
    env = os.getenv("ENV_FOR_DYNACONF", "dev01").lower()
    
    # 由于日志记录此时尚未配置，因此使用 print
    print(f"--- [config.py DEBUG] 检测到环境: '{env}'")
    
    config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
    default_settings_path = os.path.join(config_dir, 'default.py')
    env_settings_path = os.path.join(config_dir, f'{env}.py')
    
    # 加载默认设置
    if os.path.exists(default_settings_path):
        print(f"--- [config.py DEBUG] 正在加载默认设置: {default_settings_path}")
        _vars = {}
        with open(default_settings_path, 'r', encoding='utf-8') as f:
            exec(f.read(), _vars)
        for key, value in _vars.items():
            if not key.startswith('__'):
                config[key] = value

    # 加载特定于环境的设置，覆盖默认值
    if os.path.exists(env_settings_path):
        print(f"--- [config.py DEBUG] 正在加载环境设置: {env_settings_path}")
        _vars = {}
        with open(env_settings_path, 'r', encoding='utf-8') as f:
            exec(f.read(), _vars)
        for key, value in _vars.items():
            if not key.startswith('__'):
                config[key] = value
                print(f"--- [config.py DEBUG] 已从 '{env}.py' 文件中覆盖 '{key}'")
    
    print(f"--- [config.py DEBUG] 文件中的最终配置: {config}")
    return config

# 为 Pydantic 内部源类型定义类型提示，以提高可读性
PydanticSettingsSource = Callable[[type[BaseSettings]], dict[str, Any]]


class Settings(BaseSettings):
    # 为所有配置项提供类型提示和默认值
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ASR_DEVICE: str = "cpu"
    LOG_LEVEL: str = "INFO"
    
    # --- 新增：在这里声明所有与模型文件相关的配置项 ---
    MODEL_DIR: str = "models/default_model"
    RKNN_MODEL_FILE: str = "default_encoder.rknn"
    DICT_FILE: str = "dict.txt"
    VAD_MODEL_DIR: str = "/home/cat/data/asr/sense"
    AM_MVN_FILE: str = "am.mvn"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# 恢复并简化日志配置字典，以确保与Uvicorn的兼容性
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        # 只配置 root logger，uvicorn会自动继承
        "": {"handlers": ["default"], "level": "INFO"},
    },
}

settings = Settings() 