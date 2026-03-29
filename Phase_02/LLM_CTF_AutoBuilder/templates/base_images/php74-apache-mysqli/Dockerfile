FROM php:7.4-apache

# 换源 + 安装系统依赖（libpng等图片库备用）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list \
    && apt-get update && apt-get install -y \
    vim net-tools iputils-ping \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 安装 PHP MySQL 扩展（必须单独一层，不能和 apt-get install 混写）
RUN docker-php-ext-install mysqli pdo pdo_mysql

# 开启伪静态路由支持
RUN a2enmod rewrite

WORKDIR /var/www/html
RUN chown -R www-data:www-data /var/www/html

EXPOSE 80
