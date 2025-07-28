# 使用官方 Python 3.9 slim 镜像作为基础镜像
# 'slim' 版本以减小镜像体积
# 'bookworm' 对应 Debian 12，与目标操作系统匹配
FROM python:3.9-slim-bookworm

# --- 接收构建参数 ---
# 定义一个 ARG 来接收 Jenkins 传递过来的环境名称
ARG ENV_FOR_DYNACONF
# 将接收到的 ARG 设置为容器的环境变量
ENV ENV_FOR_DYNACONF=${ENV_FOR_DYNACONF}

# 设置容器内的工作目录
WORKDIR /app

# 安装应用所需的系统依赖
# - ffmpeg 对于音频处理（MP3解码）至关重要
# - 对于某些可能从源码编译的Python包，安装 build-essential 是一个好习惯
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 先复制生产环境的依赖文件，以利用 Docker 的层缓存机制
COPY requirements.prod.txt .

# 安装 requirements.prod.txt 中指定的所有包
# 我们需要为 ARM64 架构（用于 RK3562）找到正确的 tflite-runtime wheel文件。
# 下面的 URL 适用于 Debian Bullseye (Debian 11) ARM64 上的 Python 3.9，通常是兼容的。
# 如果在目标设备上失败，可能需要更新此 URL。
# 对于 Debian 12 (Bookworm)，您可能需要寻找一个更新的 wheel 文件。
RUN pip install --no-cache-dir -r requirements.prod.txt \
    && pip install --no-cache-dir --index-url https://google-coral.github.io/py-repo/ tflite-runtime

# 将应用程序的其余代码复制到容器中
COPY ./src ./src
COPY ./wav2vec2_quantized.tflite ./

# 向容器外部暴露 8000 端口
EXPOSE 8000

# 定义运行应用程序的命令
# 服务将可以通过容器外部的 8000 端口访问
# 在 Docker 中不使用 .env 文件；配置应通过环境变量传递。
# 我们在这里直接设置模型路径。
CMD ["sh", "-c", "MODEL_PATH=/app/wav2vec2_quantized.tflite python -m src.main"] 