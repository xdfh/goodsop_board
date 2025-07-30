# -*- coding: utf-8 -*-
# 开发环境 dev03 的特定配置

# ASR 服务相关配置
ASR_DEVICE = "npu"  # 在 dev03 环境，我们优先尝试 NPU
LOG_LEVEL = "INFO"

# --- 新增：在这里定义所有生产环境的模型路径 ---
# 主模型目录，所有其他文件都将基于此路径
MODEL_DIR = "/home/cat/data/asr/FireRedASR"

# 具体的模型文件名 (相对于上面的 MODEL_DIR)
RKNN_MODEL_FILE = "firered_encoder_rk3562.rknn"
DICT_FILE = "dict.txt"

# VAD 和 MVN 文件通常与旧模型在一起，我们假设它们在 sense 目录下
# 如果您也想移动它们，请修改这里的路径
VAD_MODEL_DIR = "/home/cat/data/asr/sense"
AM_MVN_FILE = "am.mvn" 