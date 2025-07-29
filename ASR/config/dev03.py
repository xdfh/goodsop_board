# -*- coding: utf-8 -*-
# 开发环境 dev03 的特定配置

# ASR 服务相关配置
MODEL_DIR = "/home/cat/data/asr/wav2vec2-large-xlsr-53-chinese-zh-cn"
ASR_DEVICE = "npu"  # 在 dev03 环境，我们优先尝试 NPU
ASR_CHUNK_SECONDS = 60                      # 分块处理音频文件的时长（秒）

# --- 环境特定配置 ---
# 在生产环境中，日志级别应该更收敛
LOG_LEVEL = "INFO" 