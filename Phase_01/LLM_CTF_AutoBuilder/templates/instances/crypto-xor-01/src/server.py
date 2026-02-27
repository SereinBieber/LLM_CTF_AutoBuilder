# Type: Stream Cipher / XOR
# Difficulty: Easy
import os
import sys
from itertools import cycle

# 获取 FLAG
FLAG = os.environ.get('FLAG', 'flag{test_xor}').encode()
# 随机生成 4 字节密钥
KEY = os.urandom(4)


def xor_cipher(data, key):
    return bytes([a ^ b for a, b in zip(data, cycle(key))])


def main():
    print("Welcome to the XOR Encryption Service!")
    print(f"I have encrypted the FLAG with a 4-byte key.")
    print(f"Encrypted FLAG (hex): {xor_cipher(FLAG, KEY).hex()}")
    print("-" * 30)
    print("You can send me any message, and I will encrypt it with the SAME key.")

    while True:
        try:
            print("Input your message (hex):")
            line = sys.stdin.readline().strip()
            if not line: break

            # 接收用户输入并加密返回
            # 漏洞：用户输入 '00000000' 即可得到密钥流，从而解密 FLAG
            pt = bytes.fromhex(line)
            ct = xor_cipher(pt, KEY)
            print(f"Ciphertext: {ct.hex()}")
        except Exception as e:
            print("Error, bye!")
            break


if __name__ == "__main__":
    main()