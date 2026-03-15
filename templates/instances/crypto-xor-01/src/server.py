# Type: Stream Cipher / XOR
# Difficulty: Easy
import os
import sys
from itertools import cycle

FLAG = os.environ.get('FLAG', 'FLAG_PLACEHOLDER').encode()
KEY  = os.urandom(4)


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
            pt = bytes.fromhex(line)
            ct = xor_cipher(pt, KEY)
            print(f"Ciphertext: {ct.hex()}")
        except Exception:
            print("Error, bye!")
            break


if __name__ == "__main__":
    main()
