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

    // 漏洞点：输入 -1 可绕过检查（-1 < 20 为真）
    // 但 read 的第三个参数是 size_t（无符号），-1 变成极大正数导致栈溢出
    if (length > 20) {
        printf("Too long!\n");
        exit(0);
    }

    printf("Input name:\n");
    read(0, buffer, length);

    if (buffer[20] != 0) {
        get_shell();
    }
    return 0;
}
