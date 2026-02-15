# Type: Hash Length Extension Attack
# Difficulty: Medium
import os
import sys
import hashlib

# 只有服务器知道这个 SECRET
SECRET = os.environ.get('FLAG', 'flag{hash_extension_attack}').encode()


# 简单的模拟：Secret + Data
# 真实场景通常是 md5(secret + message)

def main():
    print("Welcome to the MD5 MAC Service!")
    print("Here is a sample signature for you.")

    # 原始消息
    original_msg = b"user=guest"
    # 计算签名：md5(SECRET + original_msg)
    # 假设 SECRET 长度未知，但攻击者需要爆破出来或者利用 padding 机制
    h = hashlib.md5(SECRET + original_msg)
    signature = h.hexdigest()

    print(f"Original Message: {original_msg.decode()}")
    print(f"Signature: {signature}")
    print("-" * 30)
    print("Now, give me a new message and its signature.")
    print("If you can sign 'user=admin', I will give you the FLAG.")
    print("(But you don't know the SECRET length!)")

    while True:
        try:
            print("\nInput your new message (hex):")
            msg_hex = sys.stdin.readline().strip()
            if not msg_hex: break
            new_msg = bytes.fromhex(msg_hex)

            print("Input your new signature:")
            new_sig = sys.stdin.readline().strip()

            # 服务器端验证
            # 只有当 hash(SECRET + new_msg) == new_sig 时才通过
            check = hashlib.md5(SECRET + new_msg).hexdigest()

            if check == new_sig:
                if b"user=admin" in new_msg:
                    print(f"Good job! Here is your flag: {SECRET.decode()}")  # 假设 Flag 就是 Secret
                else:
                    print("Signature valid, but you are not admin.")
            else:
                print("Invalid signature!")

        except Exception as e:
            print("Error.")
            break


if __name__ == "__main__":
    main()