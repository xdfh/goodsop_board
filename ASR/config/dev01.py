# -*- coding: utf-8 -*-
# 开发环境 dev01 的特定配置

# ASR 服务相关配置
MODEL_DIR = "D:/file/asr/wav2vec2-large-xlsr-53-chinese-zh-cn"
ASR_DEVICE = "cpu"  # dev01 环境使用 CPU
ASR_CHUNK_SECONDS = 60                      # 分块处理音频文件的时长（秒）

# 在本地开发时，建议使用模型的绝对路径以避免混淆
# import os
# MODEL_PATH = os.path.abspath("E:/workspace/cursor/ASR/wav2vec2_quantized.tflite")
# MODEL_PATH = "D:/file/asr/wav2vec2-large-xlsr-53-chinese-zh-cn_float16_20250728-170216.tflite"    # 或保持默认的相对路径

# --- 环境特定配置 ---
# 例如，开启更详细的日志以方便调试
LOG_LEVEL = "DEBUG" 