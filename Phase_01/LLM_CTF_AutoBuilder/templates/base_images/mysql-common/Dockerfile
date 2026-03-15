FROM mysql:5.7

# 解决 CTF 题目中可能出现的中文 Flag 或提示乱码问题
RUN echo "[mysqld]\ncharacter-set-server=utf8mb4\ncollation-server=utf8mb4_unicode_ci" >> /etc/mysql/my.cnf

EXPOSE 3306