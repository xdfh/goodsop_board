# Stage 1: Base image with build tools if needed
# For now, we are doing a single-stage build for simplicity.

# Stage 2: Production environment
# 恢复使用国内镜像源，以解决网络超时问题
FROM docker.m.daocloud.io/python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量，确保Python按预期运行
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV ENV_FOR_DYNACONF="dev03"

# 安装系统依赖
# libatomic1: for some cv/vision libraries
# git: for potential future use or cloning private packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libatomic1 \
    git \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 为 pip 和 git 配置代理（如果需要）
# RUN git config --global http.proxy http://your-proxy-server:port
# RUN pip config set global.index-url http://your-pypi-mirror/simple

# 将依赖文件复制到工作目录
COPY requirements.prod.txt .

# 安装 Python 依赖
# 使用 --no-cache-dir 来减小镜像体积
RUN pip install --no-cache-dir -r requirements.prod.txt

# 复制本地依赖库并安装
# 修正路径：直接从构建上下文的根目录复制 libs
COPY libs ./libs
RUN pip install --no-cache-dir /app/libs/*.whl

# 复制配置文件和源代码
# 修正路径：直接从构建上下文的根目录复制
COPY config ./config
COPY src ./src

# 暴露服务端口
EXPOSE 8000

# 最终的、健壮的启动命令
# 使用 python -m uvicorn 的方式启动，可以更好地处理模块路径
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"] 