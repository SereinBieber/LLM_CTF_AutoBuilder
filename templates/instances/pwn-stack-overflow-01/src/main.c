// Type: Stack Buffer Overflow
// Difficulty: Easy
// Description: Classic gets() vulnerability. Redirect code execution to 'backdoor'.

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

// 后门函数：选手需要跳转到这里
void backdoor() {
    printf("You got it!\n");
    system("/bin/sh");
}

void vulnerable_function() {
    char buffer[64];
    printf("Please input your magic message: \n");
    // 漏洞点：gets 不限制长度，可覆盖返回地址
    gets(buffer); 
}

int main() {
    // 关闭缓冲区，防止 I/O 延迟
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    
    printf("Welcome to the Stack Overflow Challenge!\n");
    vulnerable_function();
    return 0;
}