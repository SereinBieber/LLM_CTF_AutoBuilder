// Type: ROP (Return Oriented Programming)
// Difficulty: Medium
// Description: NX is enabled. You can't execute shellcode. Construct a ROP chain!

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

// 辅助字符串，存在于二进制中，选手需要找到它的地址
char *shell = "/bin/sh";

void vulnerable_function() {
    char buffer[64];
    printf("Can you control the instruction pointer (RIP)?\n");
    printf("Input: \n");
    // 漏洞点：典型栈溢出，但 NX 开启无法直接执行 shellcode
    read(0, buffer, 0x100);
}

// "无用"函数，但把 system 链接进了程序
// 选手需要用 ROP 跳转到 system，并把 shell 字符串地址作为参数
void useless_function() {
    system("echo 'This is useless'");
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    printf("Welcome to ROP Challenge!\n");
    vulnerable_function();
    return 0;
}
