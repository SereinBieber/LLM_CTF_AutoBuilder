# Type: Public Key / RSA LSB Oracle
# Difficulty: Hard
import os
import sys
from Crypto.Util.number import getPrime, bytes_to_long

FLAG = os.environ.get('FLAG', 'FLAG_PLACEHOLDER').encode()
m    = bytes_to_long(FLAG)

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
            c_input  = int(line)
            m_output = pow(c_input, d, n)
            # 漏洞点：只泄露最低位，攻击者可用二分法还原明文
            print(f"The last bit of plaintext is: {m_output & 1}")
        except Exception:
            break


if __name__ == "__main__":
    main()
