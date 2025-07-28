# config/dev03.py

# --- DEV03 环境配置 (通常用于生产或特定部署) ---
# 在此文件中设置的所有值，将会覆盖 default.py 中的同名配置。

# --- ASR 服务相关配置 ---
ASR_DEVICE = "npu"                          # 计算设备 (cpu, gpu, npu)
ASR_MODEL_PRECISION = "INT8"                # 模型精度 (INT4, INT8, FP16, etc.)
ASR_CHUNK_SECONDS = 60                      # 分块处理音频文件的时长（秒）

# 在生产环境中，通常使用相对路径，因为模型文件会被一同打包进 Docker 镜像
MODEL_PATH = "/home/cat/data/asr/wav2vec2_quantized.tflite"


# --- 环境特定配置 ---
# 在生产环境中，日志级别应该更收敛
LOG_LEVEL = "INFO" 