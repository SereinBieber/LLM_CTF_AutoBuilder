// Type: Heap Use-After-Free (UAF)
// Difficulty: Hard
// Description: A simple note management system with UAF vulnerability.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Note {
    void (*print_func)();
    char *content;
};

void good_print() {
    printf("This is a normal note.\n");
}

void hack_print() {
    printf("Hacked! Here is your shell.\n");
    system("/bin/sh");
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    
    // 分配一个结构体
    struct Note *p = malloc(sizeof(struct Note));
    p->print_func = good_print;
    p->content = "Hello";
    
    printf("Note created.\n");
    
    // 释放内存，但没有将指针 p 置为 NULL (UAF 根源)
    free(p);
    
    // 再次分配内存，系统可能会分配到刚刚释放的那块区域
    // 攻击者如果能控制这块内存的内容，就可以覆盖 print_func 指针
    struct Note *q = malloc(sizeof(struct Note));
    q->print_func = hack_print; // 模拟被攻击者修改
    
    // 再次调用 p，实际上是在操作 q 的内存
    p->print_func(); 
    
    return 0;
}