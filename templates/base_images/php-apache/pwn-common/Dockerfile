# 选用 Ubuntu 20.04 作为主流 Pwn 环境 (对应 Glibc 2.31)
FROM ubuntu:20.04

# 避免 apt 安装时的交互式询问
ENV DEBIAN_FRONTEND=noninteractive

# 换源并安装核心工具
# gcc: 编译器
# socat: 网络转发工具 (Pwn题的灵魂)
# make: 自动化构建工具
RUN sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list \
    && apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    socat \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 创建低权限用户 ctf，防止选手拿到 root
RUN useradd -m ctf

# 设置工作目录
WORKDIR /app

# 默认暴露端口 (虽然 compose 会映射，但这里声明一下符合规范)
EXPOSE 9999