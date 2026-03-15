# 选用 Python 3.9 Alpine 版，体积小且支持数学库
FROM python:3.9-alpine

# 换源，加速构建
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

# 1. 安装系统级依赖 (gcc 和 musl-dev 是为了编译某些数学库)
# 2. 安装 socat (用于端口转发，把 Python 脚本变成网络服务)
RUN apk add --no-cache gcc musl-dev socat

# 3. 预装 CTF 密码学核心库 pycryptodome
# 这样以后生成题目时，不需要再重复下载安装，启动速度极快
RUN pip install --no-cache-dir pycryptodome -i https://mirrors.aliyun.com/pypi/simple/

# 设置工作目录
WORKDIR /app

# 声明端口
EXPOSE 9999