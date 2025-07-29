# -*- coding: utf-8 -*-

import os
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, Any

# 这是一个辅助函数，用于从 .py 文件加载配置
def py_file_settings(settings: BaseSettings) -> dict:
    config = {}
    
    # 1. 确定环境并找到配置文件
    # 我们继续使用 Jenkins/Dockerfile 中传入的 ENV_FOR_DYNACONF 环境变量
    env = os.getenv("ENV_FOR_DYNACONF", "dev01").lower()
    config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
    
    default_settings_path = os.path.join(config_dir, 'default.py')
    env_settings_path = os.path.join(config_dir, f'{env}.py')
    
    logging.info("-" * 50)
    logging.info(f"INFO: 检测到当前环境为: '{env}'")
    
    # 2. 从 default.py 加载配置
    if os.path.exists(default_settings_path):
        logging.info(f"INFO: 准备加载默认配置文件: {default_settings_path}")
        # 使用 exec 读取 .py 文件中的变量
        _vars = {}
        with open(default_settings_path, 'r', encoding='utf-8') as f:
            exec(f.read(), _vars)
        for key, value in _vars.items():
            if not key.startswith('__'):
                config[key] = value
    
    # 3. 从环境特定的 .py 文件加载配置，并覆盖默认值
    if os.path.exists(env_settings_path):
        logging.info(f"INFO: 准备加载环境配置文件: {env_settings_path}")
        _vars = {}
        with open(env_settings_path, 'r', encoding='utf-8') as f:
            exec(f.read(), _vars)
        for key, value in _vars.items():
            if not key.startswith('__'):
                config[key] = value
    else:
        logging.warning(f"WARN: 未找到环境 '{env}' 的特定配置文件: {env_settings_path}")

    logging.info("-" * 50)
    return config


class Settings(BaseSettings):
    # 为所有配置项提供类型提示和默认值
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    MODEL_DIR: str = "models/default_chinese_model"
    ASR_DEVICE: str = "cpu"
    
    # Logging configuration
    LOGGING_CONFIG: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(asctime)s - %(message)s",
                "use_colors": None,
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "": {"handlers": ["default"], "level": logging.INFO},
            "uvicorn.error": {"level": logging.INFO},
            "uvicorn.access": {"handlers": ["access"], "level": logging.INFO, "propagate": False},
        },
    }

    model_config = SettingsConfigDict(
        env_file_encoding='utf-8',
        # Pydantic-settings will call this function to load settings from python files.
        # @field: ... 表示这是 pydantic-settings 的一个特殊功能
        custom_settings_source=py_file_settings
    )


settings = Settings() 