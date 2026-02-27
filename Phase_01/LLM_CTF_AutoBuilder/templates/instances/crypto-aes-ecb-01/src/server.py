# Type: Block Cipher / AES-ECB
# Difficulty: Medium
import os
import sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

FLAG = os.environ.get('FLAG', 'flag{aes_ecb_leak}').encode()
# 随机 16 字节密钥
KEY = os.urandom(16)


def aes_encrypt(plaintext):
    cipher = AES.new(KEY, AES.MODE_ECB)
    # 漏洞点：将用户输入和 FLAG 拼接在一起加密
    # 用户可以通过控制输入长度，把 FLAG 的每个字节挤到块边界上进行爆破
    return cipher.encrypt(pad(plaintext + FLAG, 16))


def main():
    print("Welcome to the AES-ECB Oracle!")
    print("I will encrypt: input + FLAG")

    while True:
        try:
            print("Input your payload (hex):")
            line = sys.stdin.readline().strip()
            if not line: break

            pt = bytes.fromhex(line)
            ct = aes_encrypt(pt)
            print(f"Ciphertext: {ct.hex()}")
        except:
            break


if __name__ == "__main__":
    main()