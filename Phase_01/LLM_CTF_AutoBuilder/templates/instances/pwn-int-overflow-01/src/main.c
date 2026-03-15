// Type: Integer Overflow
// Difficulty: Medium

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void get_shell() {
    system("/bin/sh");
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    int length;
    char buffer[20];

    printf("How long is your name?\n");
    scanf("%d", &length);

    // 漏洞点：如果输入 -1，可以通过此检查 (因为 -1 < 20)
    // 但在 read 函数中，length 被解释为无符号大整数，导致栈溢出
    if (length > 20) {
        printf("Too long!\n");
        exit(0);
    }

    printf("Input name:\n");
    // read 的第三个参数是 size_t (unsigned int)
    read(0, buffer, length);

    if (buffer[20] != 0) { // 简单模拟溢出后的行为
        get_shell();
    }
    return 0;
}