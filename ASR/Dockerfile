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

# 复制项目的依赖文件
# 将生产环境的依赖文件复制到容器中
COPY ASR/requirements.prod.txt .

# 安装依赖
# --no-cache-dir: 不缓存包，减小镜像大小
# -i: 指定使用国内的 PyPI 镜像源，加速下载
# --index-url: 为 tflite-runtime 指定特殊的包索引
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.prod.txt \
    && pip install --no-cache-dir --index-url https://google-coral.github.io/py-repo/ tflite-runtime

# 复制配置文件和应用程序代码
# 将 config 目录完整复制过去
COPY ASR/config ./config
# 将 src 目录完整复制过去
COPY ASR/src ./src

# 向容器外部暴露 8000 端口
EXPOSE 8000

# 容器启动时执行的命令
# 使用 python -m src.main 来启动 uvicorn 服务
CMD ["python", "-m", "src.main"] 