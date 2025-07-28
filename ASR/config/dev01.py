# config/dev01.py

# --- DEV01 环境配置 ---
# 在此文件中设置的所有值，将会覆盖 default.py 中的同名配置。

# --- ASR 服务相关配置 ---
ASR_DEVICE = "gpu"                          # 计算设备 (cpu, gpu, npu)
ASR_MODEL_PRECISION = "INT8"                # 模型精度 (INT4, INT8, FP16, etc.)
ASR_CHUNK_SECONDS = 60                      # 分块处理音频文件的时长（秒）

# 在本地开发时，建议使用模型的绝对路径以避免混淆
# import os
# MODEL_PATH = os.path.abspath("E:/workspace/cursor/ASR/wav2vec2_quantized.tflite")
MODEL_PATH = "D:/file/asr/wav2vec2_quantized.tflite"    # 或保持默认的相对路径

# --- 环境特定配置 ---
# 例如，开启更详细的日志以方便调试
LOG_LEVEL = "DEBUG" 