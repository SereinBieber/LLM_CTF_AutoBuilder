# Type: Public Key / RSA LSB Oracle
# Difficulty: Hard
import os
import sys
from Crypto.Util.number import getPrime, bytes_to_long

FLAG = os.environ.get('FLAG', 'flag{rsa_lsb_oracle}').encode()
m = bytes_to_long(FLAG)

# 生成 RSA 参数
p = getPrime(512)
q = getPrime(512)
n = p * q
e = 65537
d = pow(e, -1, (p - 1) * (q - 1))


def main():
    print("Welcome to RSA Parity Oracle!")
    print(f"n = {n}")
    print(f"e = {e}")
    print(f"Encrypted Flag c = {pow(m, e, n)}")
    print("-" * 30)

    while True:
        try:
            print("Give me a ciphertext (integer):")
            line = sys.stdin.readline().strip()
            if not line: break

            c_input = int(line)
            # 解密
            m_output = pow(c_input, d, n)

            # 漏洞点：只泄露最后一位（奇偶性）
            # 攻击者可以利用这一点进行二分查找
            print(f"The last bit of plaintext is: {m_output & 1}")
        except:
            break


if __name__ == "__main__":
    main()