#!/usr/bin/env python3
# db-redis-unauth-01 flag 初始化脚本
# 容器启动后执行，把 FLAG 写入 Redis 的 flag 键
import os
import time
import redis

FLAG = os.environ.get('FLAG', 'FLAG_PLACEHOLDER')

# 等 Redis 启动完
time.sleep(2)

try:
    r = redis.Redis(host='localhost', port=6379)
    r.set('flag', FLAG)
    print(f"[+] Flag written to Redis key 'flag': {FLAG}")
except Exception as e:
    print(f"[-] Failed to write flag: {e}")
