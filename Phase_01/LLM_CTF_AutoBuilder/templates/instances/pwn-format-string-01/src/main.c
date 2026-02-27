// Type: Format String Vulnerability
// Difficulty: Medium
// Description: printf(buf) allows memory leak and arbitrary write.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int secret_value = 0;

void get_flag() {
    printf("Congratulation! Here is your shell.\n");
    system("/bin/sh");
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    char buffer[100];

    printf("What's your name?\n");
    read(0, buffer, sizeof(buffer));

    printf("Hello, ");
    // 漏洞点：直接打印 buffer，没有格式化参数
    // 攻击者输入 %x %x 可泄露内存，输入 %n 可修改 secret_value
    printf(buffer); 
    
    if (secret_value == 0x1337) {
        get_flag();
    } else {
        printf("\nBye!\n");
    }
    return 0;
}