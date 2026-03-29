# Type: Block Cipher / AES-ECB Byte-at-a-time
# Difficulty: Medium
import os
import sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

FLAG = os.environ.get('FLAG', 'FLAG_PLACEHOLDER').encode()
KEY  = os.urandom(16)


def aes_encrypt(plaintext):
    cipher = AES.new(KEY, AES.MODE_ECB)
    # 漏洞点：将用户输入和FLAG拼接后加密
    # 控制输入长度可将FLAG每字节挤到块边界进行逐字节爆破
    return cipher.encrypt(pad(plaintext + FLAG, 16))


def main():
    print("Welcome to the AES-ECB Oracle!")
    print("I will encrypt: YOUR_INPUT + FLAG")

    while True:
        try:
            print("Input your payload (hex):")
            line = sys.stdin.readline().strip()
            if not line: break
            pt  = bytes.fromhex(line)
            ct  = aes_encrypt(pt)
            print(f"Ciphertext: {ct.hex()}")
        except Exception:
            break


if __name__ == "__main__":
    main()
