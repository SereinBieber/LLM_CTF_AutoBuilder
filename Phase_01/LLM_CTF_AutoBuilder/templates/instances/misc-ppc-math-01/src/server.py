# Type: PPC Math
# Difficulty: Easy
import sys
import random
import time
import signal


# 30秒超时处理
def timeout(signum, frame):
    print("\n⏰ Time's up!")
    sys.exit(0)


def main():
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(30)

    print("Quick Math: Answer 50 questions in 30s!")
    target = 50
    correct = 0

    for i in range(target):
        a = random.randint(1, 100)
        b = random.randint(1, 100)
        ans = a + b

        print(f"[{i + 1}/{target}] {a} + {b} = ?")
        sys.stdout.flush()

        try:
            user = sys.stdin.readline().strip()
            if int(user) == ans:
                correct += 1
            else:
                print("Wrong!")
                sys.exit(0)
        except:
            sys.exit(0)

    print(f"🎉 Flag: {os.environ.get('FLAG', 'flag{ppc_success}')}")


if __name__ == "__main__":
    import os

    main()