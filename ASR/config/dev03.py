# -*- coding: utf-8 -*-
# 开发环境 dev03 的特定配置

# ASR 服务相关配置
MODEL_DIR = "/home/cat/data/asr/sense"
ASR_DEVICE = "npu"  # 在 dev03 环境，我们优先尝试 NPU

# --- 环境特定配置 ---
# 在生产环境中，日志级别应该更收敛
LOG_LEVEL = "INFO" 