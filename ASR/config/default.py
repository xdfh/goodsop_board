# config/default.py

# ASR 服务相关配置
ASR_DEVICE = "cpu"  # 计算设备 (cpu, gpu, npu)
ASR_MODEL_PRECISION = "INT8"  # 模型精度 (INT4, INT8, FP16, etc.)
ASR_CHUNK_SECONDS = 15  # 分块处理音频文件的时长（秒）
MODEL_PATH = "wav2vec2_quantized.tflite"  # 默认模型路径

# API 服务相关配置
HOST = "0.0.0.0"
PORT = 8000 