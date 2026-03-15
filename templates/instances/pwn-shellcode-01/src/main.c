// Type: Shellcode Execution
// Difficulty: Easy
// Description: I will execute whatever you send me. Give me your shellcode!

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);

    printf("Welcome to the Shellcode Runner!\n");
    printf("I have allocated a RWX memory for you.\n");

    // mmap 分配一块可读可写可执行的内存
    void *ptr = mmap(0, 0x1000,
                     PROT_READ | PROT_WRITE | PROT_EXEC,
                     MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (ptr == MAP_FAILED) {
        perror("mmap");
        return 1;
    }

    printf("Send me your shellcode: \n");
    read(0, ptr, 0x1000);
    printf("Executing your code...\n");

    // 直接跳转执行用户输入的机器码
    ((void(*)())ptr)();

    return 0;
}
