# Type: PyJail
# Difficulty: Medium
import sys


def main():
    print("Welcome to Python Jail!")
    print("Enter python code to run (no 'import', 'eval').")

    # 黑名单过滤
    blacklist = ['import', 'eval', 'exec', '__import__', 'open']

    while True:
        try:
            sys.stdout.write(">>> ")
            sys.stdout.flush()
            line = sys.stdin.readline().strip()
            if not line: break

            if any(w in line for w in blacklist):
                print("🚫 Forbidden!")
                continue

            # 在受限空间执行
            exec(line, {'__builtins__': None}, {})
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()