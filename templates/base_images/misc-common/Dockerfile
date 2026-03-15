FROM python:3.9-alpine

# 换源
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

# 1. 安装系统依赖
# socat/bash: 基础工具
# jpeg-dev/zlib-dev/gcc/musl-dev: 编译 Pillow 图片库必须的依赖
RUN apk add --no-cache socat bash coreutils vim jpeg-dev zlib-dev gcc musl-dev

# 2. 安装 Python 图片处理库 Pillow
RUN pip install --no-cache-dir Pillow -i https://mirrors.aliyun.com/pypi/simple/

# 创建用户
RUN adduser -D -u 1000 ctf
WORKDIR /app
EXPOSE 9999