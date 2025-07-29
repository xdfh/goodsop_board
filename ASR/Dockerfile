# 使用国内的 Python 3.9 slim 镜像作为基础镜像，以规避网络问题
# 'slim' 版本以减小镜像体积
# 'bookworm' 对应 Debian 12，与目标操作系统匹配
FROM docker.m.daocloud.io/python:3.9-slim-bookworm

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
# -i: 将唯一的索引指向内部 Nexus 的 pypi-group，它现在可以提供所有来源的包
# --trusted-host: 信任非 https 的 Nexus 源
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    -r requirements.prod.txt \
    -i http://192.168.1.161:8081/repository/pypi-group/simple \
    --trusted-host 192.168.1.161

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