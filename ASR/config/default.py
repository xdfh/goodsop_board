# -*- coding: utf-8 -*-
# 默认配置文件

# 服务器配置
HOST = "0.0.0.0"
PORT = 8000

# ASR 服务相关配置
MODEL_DIR = "models/default_model"  # 默认模型目录
ASR_DEVICE = "cpu"
LOG_LEVEL = "INFO"

# --- 新增：将所有模型文件名配置化 ---
RKNN_MODEL_FILE = "default_encoder.rknn"
DICT_FILE = "dict.txt"
VAD_MODEL_DIR = "models/default_model" # VAD 模型通常与主模型放在一起
AM_MVN_FILE = "am.mvn" 