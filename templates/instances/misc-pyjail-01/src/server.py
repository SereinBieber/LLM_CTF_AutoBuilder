# Type: Python Jail
# Difficulty: Medium
import os
import sys

FLAG = os.environ.get('FLAG', 'FLAG_PLACEHOLDER')
if FLAG and FLAG != 'FLAG_PLACEHOLDER':
    with open('/flag', 'w') as f:
        f.write(FLAG)

BLACKLIST = ['import', 'eval', 'exec', '__import__', 'open', 'os', 'sys']


def main():
    print("Welcome to Python Jail!")
    print("Enter python code to run.")
    print(f"Blacklist: {BLACKLIST}")
    print("The flag is at /flag, can you read it?")

    while True:
        try:
            sys.stdout.write(">>> ")
            sys.stdout.flush()
            line = sys.stdin.readline().strip()
            if not line: break

            if any(w in line for w in BLACKLIST):
                print("🚫 Forbidden!")
                continue

            # 漏洞：__builtins__=None 但可通过 __class__.__mro__ 链绕过
            exec(line, {'__builtins__': None}, {})
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
