#!/bin/sh
# build.sh — 编译时将 FLAG 注入二进制
# 由 docker-compose command 调用，环境变量 FLAG 已由 compose 注入

set -e

FLAG="${FLAG:-flag{placeholder_flag_value}}"

echo "[*] Building challenge binary with flag: ${FLAG}"

gcc -O2 -fno-stack-protector \
    -DFLAG_VALUE="\"${FLAG}\"" \
    -o challenge main.c

strip challenge

echo "[+] Build complete: $(ls -lh challenge | awk '{print $5, $9}')"
