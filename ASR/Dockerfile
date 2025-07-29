# 使用官方 Python 3.9 slim-bookworm 镜像作为基础
# slim 版本包含运行 Python 应用所需的最少包
# bookworm 是 Debian 12 的代号
FROM python:3.9-slim-bookworm

# 设置非交互式前端，防止 apt-get 在构建过程中请求用户输入
ENV DEBIAN_FRONTEND=noninteractive

# 新增：更换为国内的 apt 软件源以加速构建
RUN sed -i 's|http://deb.debian.org/debian/|http://mirrors.tuna.tsinghua.edu.cn/debian/|g' /etc/apt/sources.list.d/debian.sources

# 安装 ffmpeg 和其他可能需要的系统依赖
# --no-install-recommends: 不安装推荐的包，保持镜像体积小
# apt-get clean && rm -rf /var/lib/apt/lists/*: 清理 apt 缓存，减小最终镜像大小
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 新增：将底层的 NPU 动态库复制到系统标准库路径，以便 Python 包装器能够找到它
COPY ASR/libs/librknnrt.so /usr/lib/

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

# 复制本地依赖库
COPY ./ASR/libs /app/libs

# 运行 pip install 命令安装所有依赖
# --no-cache-dir: 不使用缓存，确保每次都是最新的安装
# -r requirements.prod.txt: 从文件中安装依赖
# -i: 将唯一的索引指向内部 Nexus 的 pypi-group，它现在可以提供所有来源的包
# --trusted-host: 信任非 https 的 Nexus 源
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    -r requirements.prod.txt \
    -i http://192.168.1.161:8081/repository/pypi-group/simple \
    --trusted-host 192.168.1.161 && \
    pip install --no-cache-dir \
    /app/libs/*.whl \
    -i http://192.168.1.161:8081/repository/pypi-group/simple \
    --trusted-host 192.168.1.161

# 向容器外部暴露 8000 端口
EXPOSE 8000

# 容器启动时执行的命令
# 使用 python -m src.main 来启动 uvicorn 服务
CMD ["python", "-m", "src.main"] 