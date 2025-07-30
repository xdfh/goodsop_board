# -*- coding: utf-8 -*-

import os
import logging
from functools import partial
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, Any, Tuple, Callable

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
    VAD_MODEL_DIR: str = "models/default_model"
    AM_MVN_FILE: str = "am.mvn"

    # 日志配置
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

    model_config = SettingsConfigDict(env_file_encoding='utf-8')

    # 2. 这是在 pydantic-settings 中添加自定义设置源的正确方法
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticSettingsSource,
        env_settings: PydanticSettingsSource,
        dotenv_settings: PydanticSettingsSource,
        file_secret_settings: PydanticSettingsSource,
    ) -> Tuple[PydanticSettingsSource, ...]:
        return (
            # 使用 functools.partial 来“预填充”我们的加载函数所需的 settings_cls 参数
            partial(py_file_settings_source, settings_cls),
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )

settings = Settings() 