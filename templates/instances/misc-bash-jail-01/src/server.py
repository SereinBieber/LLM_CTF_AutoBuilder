# Type: Bash Jail
# Difficulty: Easy
import os
import sys


def main():
    print("Welcome to Restricted Shell!")
    print("Rules: No spaces, no slashes, no 'cat'.")

    while True:
        try:
            sys.stdout.write("shell$ ")
            sys.stdout.flush()
            cmd = sys.stdin.readline().strip()
            if not cmd: break

            # 过滤逻辑
            if ' ' in cmd or '/' in cmd or 'cat' in cmd:
                print("🚫 Command blocked!")
                continue

            # 调用系统 Shell 执行
            os.system(cmd)
        except:
            break


if __name__ == "__main__":
    main()