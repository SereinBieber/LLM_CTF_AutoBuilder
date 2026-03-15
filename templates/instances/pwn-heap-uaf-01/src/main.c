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

    struct Note *p = malloc(sizeof(struct Note));
    p->print_func = good_print;
    p->content    = "Hello";
    printf("Note created.\n");

    // 漏洞点：free 后未将 p 置 NULL
    free(p);

    // 重新分配同大小内存，可能拿到同一块堆
    // 攻击者控制此块内容即可覆盖 print_func 指针
    struct Note *q = malloc(sizeof(struct Note));
    q->print_func  = hack_print;

    // 通过悬空指针 p 调用，实际执行了 hack_print
    p->print_func();

    return 0;
}
