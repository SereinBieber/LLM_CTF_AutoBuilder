# Type: PPC (Programming Puzzle & Challenge) - Math
# Difficulty: Easy
import os
import sys
import random
import signal

FLAG = os.environ.get('FLAG', 'FLAG_PLACEHOLDER')


def timeout(signum, frame):
    print("\n⏰ Time's up!")
    sys.exit(0)


def main():
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(30)

    print("Quick Math: Answer 50 questions in 30 seconds!")
    target = 50

    for i in range(target):
        a   = random.randint(1, 100)
        b   = random.randint(1, 100)
        ans = a + b

        print(f"[{i + 1}/{target}] {a} + {b} = ?")
        sys.stdout.flush()

        try:
            user = sys.stdin.readline().strip()
            if int(user) == ans:
                continue
            else:
                print("Wrong! Game over.")
                sys.exit(0)
        except Exception:
            sys.exit(0)

    print(f"🎉 Congratulations! Flag: {FLAG}")


if __name__ == "__main__":
    main()
