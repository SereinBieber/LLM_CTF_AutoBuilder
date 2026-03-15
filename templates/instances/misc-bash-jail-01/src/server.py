# Type: Bash Jail
# Difficulty: Easy
import os
import sys

# 把 FLAG 写入 /flag，选手需要绕过限制读取它
FLAG = os.environ.get('FLAG', 'FLAG_PLACEHOLDER')
if FLAG and FLAG != 'FLAG_PLACEHOLDER':
    with open('/flag', 'w') as f:
        f.write(FLAG)


def main():
    print("Welcome to Restricted Shell!")
    print("Rules: No spaces, no slashes, no 'cat'.")
    print("The flag is somewhere on this system... find it!")

    while True:
        try:
            sys.stdout.write("shell$ ")
            sys.stdout.flush()
            cmd = sys.stdin.readline().strip()
            if not cmd: break

            # 过滤逻辑（漏洞：用 $IFS 绕过空格，用 base64 绕过 cat）
            if ' ' in cmd or '/' in cmd or 'cat' in cmd:
                print("🚫 Command blocked!")
                continue

            os.system(cmd)
        except Exception:
            break


if __name__ == "__main__":
    main()
