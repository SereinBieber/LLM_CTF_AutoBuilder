FROM php:7.4-apache

# 换源并安装常用工具 (模拟真实服务器环境)
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list \
    && apt-get update && apt-get install -y \
    net-tools \
    iputils-ping \
    vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 启用 Apache Rewrite 模块
RUN a2enmod rewrite

# 设置 Web 根目录权限
WORKDIR /var/www/html
RUN chown -R www-data:www-data /var/www/html

# 默认暴露端口
EXPOSE 80