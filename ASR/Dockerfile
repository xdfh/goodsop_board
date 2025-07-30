# 使用国内的 Python 3.9 slim 镜像作为基础镜像，以规避网络问题
# 'slim' 版本以减小镜像体积
# 'bookworm' 对应 Debian 12，与目标操作系统匹配
FROM docker.m.daocloud.io/python:3.9-slim-bookworm

# 设置非交互式前端，防止 apt-get 在构建过程中请求用户输入
ENV DEBIAN_FRONTEND=noninteractive

# 接收构建时参数
ARG APP_ENV
# 将构建时参数设置为容器的环境变量，确保名称与 config.py 中读取的一致
ENV ENV_FOR_DYNACONF=${APP_ENV}

# 新增调试探针：在构建日志中打印出环境变量，以确认其是否被正确传递
RUN echo ">>> Dockerfile: Building for APP_ENV=${APP_ENV}"

# 新增：彻底更换为国内的 apt 软件源以加速构建
RUN echo "Types: deb\n\
URIs: https://mirrors.tuna.tsinghua.edu.cn/debian/\n\
Suites: bookworm bookworm-updates bookworm-backports\n\
Components: main contrib non-free non-free-firmware\n\
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg\n\
\n\
Types: deb\n\
URIs: https://mirrors.tuna.tsinghua.edu.cn/debian-security/\n\
Suites: bookworm-security\n\
Components: main contrib non-free non-free-firmware\n\
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg\n\
" > /etc/apt/sources.list.d/debian.sources

# 安装 ffmpeg 和其他可能需要的系统依赖
# --- 最终修正：为新版 RKNN 驱动添加 libatomic1 依赖 ---
# --no-install-recommends: 不安装推荐的包，保持镜像体积小
# apt-get clean && rm -rf /var/lib/apt/lists/*: 清理 apt 缓存，减小最终镜像大小
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libatomic1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# --- 依赖项设置 ---

# 1. 复制并注册底层的 NPU 动态库
COPY ASR/libs/librknnrt.so /usr/lib/
RUN ldconfig

# 2. 复制所有依赖相关的文件
COPY ASR/requirements.prod.txt .
COPY ./ASR/libs /app/libs

# 3. 一次性安装所有 Python 依赖 (来自 requirements.txt 和 .whl 文件)
#    这可以更好地利用 Docker 缓存
# 安装 Python 依赖
# 我们将安装分为两步，以解决 torch 的 Illegal instruction 和依赖冲突问题

# 步骤 1: 安装通用依赖，包括从 git 克隆并安装 wenet
RUN pip install --no-cache-dir --upgrade pip -i http://192.168.1.161:8081/repository/pypi-group/simple --trusted-host 192.168.1.161 && \
    pip install --no-cache-dir -r requirements.prod.txt -i http://192.168.1.161:8081/repository/pypi-group/simple --trusted-host 192.168.1.161 && \
    pip install --no-cache-dir /app/libs/*.whl -i http://192.168.1.161:8081/repository/pypi-group/simple --trusted-host 192.168.1.161 && \
    git clone https://github.com/wenet-e2e/wenet.git && \
    pip install --no-cache-dir --no-deps -e ./wenet -i http://192.168.1.161:8081/repository/pypi-group/simple --trusted-host 192.168.1.161

# 步骤 2: 安装 torch 和 torchaudio
# 我们最后安装 torch，以确保它的依赖不会被其他包覆盖，从而解决依赖冲突
# 我们降级到 2.2.0，尝试解决 Illegal instruction 问题，这可能是由于新版本 PyTorch 的指令集与 RK3562 CPU 不兼容
RUN pip install --no-cache-dir torch==2.2.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cpu

# 设置工作目录
WORKDIR /

# --- 应用程序代码 ---

# 复制配置文件和应用程序源代码
# 将它们放在依赖安装之后，这样代码变更时不会导致依赖重新安装
COPY ASR/config ./config
COPY ASR/src ./src

# --- 运行配置 ---

# 向容器外部暴露 8000 端口
EXPOSE 8000

# 容器启动时执行的命令
# 使用 python -m src.main 来启动 uvicorn 服务
CMD ["python", "-m", "src.main"] 