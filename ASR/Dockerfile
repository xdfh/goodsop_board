# Stage 2: Production environment
# 恢复使用国内镜像源，以解决网络超时问题
FROM docker.m.daocloud.io/python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量，确保Python按预期运行
# 修正 ENV 语法为 key=value 格式
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENV_FOR_DYNACONF="dev03"

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libatomic1 \
    git \
    ffmpeg \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 将依赖文件复制到工作目录
COPY ASR/requirements.prod.txt .

# 安装 Python 依赖，恢复使用本地镜像源以解决网络问题
RUN pip install --no-cache-dir -r requirements.prod.txt \
    -i http://192.168.1.161:8081/repository/pypi-group/simple \
    --trusted-host 192.168.1.161

# 关键修复：独立安装 torch 和 torchaudio，使用其官方源
RUN pip install --no-cache-dir torch==2.2.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cpu

# 复制本地依赖库并安装
COPY ASR/libs ./libs
RUN pip install --no-cache-dir /app/libs/*.whl \
    -i http://192.168.1.161:8081/repository/pypi-group/simple \
    --trusted-host 192.168.1.161

# 复制配置文件和源代码
COPY ASR/config ./config
COPY ASR/src ./src

# 暴露服务端口
EXPOSE 8000

# 最终的、健壮的启动命令
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"] 