FROM python:3.9-slim

# 换源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list \
    && pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装依赖
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 创建普通用户 (CTF 题目通常不用 root 运行)
RUN useradd -m ctf
USER ctf

EXPOSE 5000
CMD ["python", "app.py"]