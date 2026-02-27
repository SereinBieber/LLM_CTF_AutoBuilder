// Type: ROP (Return Oriented Programming)
// Difficulty: Medium
// Description: NX is enabled. You can't execute shellcode. Construct a ROP chain!

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

// 辅助字符串，存在于二进制文件中，选手需要找到它的地址
char *shell = "/bin/sh";

void vulnerable_function() {
    char buffer[64];
    printf("Can you control the instruction pointer (RIP)?\n");
    printf("Input: \n");
    // 典型的栈溢出
    read(0, buffer, 0x100);
}

// 这是一个“无用”的函数，但在 ROP 中非常重要
// 它把 system 函数链接进了程序，但没有直接调用它拿到 shell
// 选手需要强行跳转到 system 的地址，并把 shell 字符串作为参数传给它
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