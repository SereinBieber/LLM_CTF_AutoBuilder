# Type: Hash Length Extension Attack
# Difficulty: Medium
import os
import sys
import hashlib

# SECRET 是签名密钥，FLAG 是答对后的奖励，两者分开
SECRET = os.environ.get('SECRET', 'supersecretkey').encode()
FLAG   = os.environ.get('FLAG',   'FLAG_PLACEHOLDER')


def main():
    print("Welcome to the MD5 MAC Service!")
    original_msg = b"user=guest"
    h = hashlib.md5(SECRET + original_msg)
    signature = h.hexdigest()

    print(f"Original Message: {original_msg.decode()}")
    print(f"Signature: {signature}")
    print(f"Secret length hint: {len(SECRET)} bytes")
    print("-" * 30)
    print("If you can forge a valid signature for a message containing 'user=admin',")
    print("I will give you the FLAG.")

    while True:
        try:
            print("\nInput your new message (hex):")
            msg_hex = sys.stdin.readline().strip()
            if not msg_hex: break
            new_msg = bytes.fromhex(msg_hex)

            print("Input your new signature:")
            new_sig = sys.stdin.readline().strip()

            check = hashlib.md5(SECRET + new_msg).hexdigest()
            if check == new_sig:
                if b"user=admin" in new_msg:
                    print(f"Correct! Flag: {FLAG}")
                else:
                    print("Signature valid, but you are not admin.")
            else:
                print("Invalid signature!")
        except Exception:
            print("Error.")
            break


if __name__ == "__main__":
    main()
