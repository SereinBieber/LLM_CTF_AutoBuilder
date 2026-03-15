#!/bin/sh
set -e

FLAG="${FLAG:-flag{placeholder_flag_value}}"
echo "[*] Building MiniVM challenge..."

gcc -O1 -fno-stack-protector \
    -DFLAG_VALUE="\"${FLAG}\"" \
    -o challenge main.c

strip challenge
echo "[+] Build complete: $(ls -lh challenge | awk '{print $5, $9}')"
