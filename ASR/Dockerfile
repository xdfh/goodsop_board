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

#
# --- 依赖安装阶段 (已优化缓存) ---
#

# 1. 单独复制 requirements.txt
COPY ASR/requirements.prod.txt .

# 2. 安装 pip 和 requirements.txt 中的依赖
#    只要 requirements.txt 不变，这一层就会被缓存
RUN pip install --no-cache-dir --upgrade pip -i http://192.168.1.161:8081/repository/pypi-group/simple --trusted-host 192.168.1.161 && \
    pip install --no-cache-dir -r requirements.prod.txt -i http://192.168.1.161:8081/repository/pypi-group/simple --trusted-host 192.168.1.161

# 3. 单独复制本地 libs
COPY ./ASR/libs /app/libs

# 4. 安装本地 whl 包
#    只要 libs 文件夹内容不变，这一层就会被缓存
RUN pip install --no-cache-dir /app/libs/*.whl -i http://192.168.1.161:8081/repository/pypi-group/simple --trusted-host 192.168.1.161

# 5. 安装 torch 和 torchaudio (最耗时的下载)
#    这一层也稳定不变
RUN pip install --no-cache-dir torch==2.2.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cpu


# --- 应用程序代码 (经常变动) ---
#
# 将代码复制操作放在最后，这样修改代码不会破坏前面的依赖缓存
COPY ASR/config ./config
# 将 ASR/src 的内容复制到 /app/src
COPY ASR/src ./src

# 设置工作目录
WORKDIR /app

# --- 运行配置 ---

# 向容器外部暴露 8000 端口
EXPOSE 8000

# 运行应用
# 使用 python -m uvicorn 的方式启动，可以更好地处理模块路径
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"] 