/*
 * Challenge : AntiDebug Keygen
 * Type      : Reverse Engineering - Anti-Debug Techniques
 * Difficulty: Medium
 *
 * Description:
 *   A key generator protected by three layers of anti-debugging:
 *     1. ptrace self-attach detection
 *     2. /proc/self/status TracerPid check
 *     3. RDTSC timing anomaly detection
 *   Under a debugger all three trigger a decoy path that outputs a fake flag.
 *   Bypass or patch the checks to reach the real decryption routine.
 *
 * Reversing approach:
 *   Option A (static): NOP out the three guard functions in IDA/Binary Ninja,
 *                      re-run to get the real flag.
 *   Option B (dynamic): Use LD_PRELOAD to hook ptrace(); edit /proc shim;
 *                       patch RDTSC result to a constant.
 *   Option C (scripted): Extract `secret_data[]` and `decrypt_secret()` logic,
 *                        replicate decryption offline.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ptrace.h>
#include <time.h>

#ifndef FLAG_VALUE
#define FLAG_VALUE "flag{placeholder_flag_value}"
#endif

#define MAX_FLAG_LEN 64

/* ------------------------------------------------------------------ */
/*  Anti-debug layer 1: ptrace self-attach                            */
/* ------------------------------------------------------------------ */
static int ad_ptrace_check(void) {
    if (ptrace(PTRACE_TRACEME, 0, NULL, NULL) == -1) {
        /* already being traced */
        return 1;
    }
    /* detach immediately so we don't block ourselves */
    ptrace(PTRACE_DETACH, 0, NULL, NULL);
    return 0;
}

/* ------------------------------------------------------------------ */
/*  Anti-debug layer 2: /proc/self/status TracerPid                   */
/* ------------------------------------------------------------------ */
static int ad_tracerpid_check(void) {
    char  buf[512];
    int   fd;
    char *ptr;

    fd = open("/proc/self/status", O_RDONLY);
    if (fd < 0) return 0;   /* can't open → assume not traced */

    ssize_t n = read(fd, buf, sizeof(buf) - 1);
    close(fd);
    if (n <= 0) return 0;
    buf[n] = '\0';

    ptr = strstr(buf, "TracerPid:");
    if (!ptr) return 0;

    int tracer_pid = 0;
    sscanf(ptr + strlen("TracerPid:"), "%d", &tracer_pid);
    return (tracer_pid != 0);
}

/* ------------------------------------------------------------------ */
/*  Anti-debug layer 3: RDTSC timing anomaly                          */
/* ------------------------------------------------------------------ */
static int ad_timing_check(void) {
#if defined(__x86_64__) || defined(__i386__)
    uint32_t lo1, hi1, lo2, hi2;
    uint64_t t1, t2;

    __asm__ volatile ("rdtsc" : "=a"(lo1), "=d"(hi1));
    /* a tiny nop sled; a single-step debugger adds enormous overhead */
    for (volatile int i = 0; i < 100; i++) { __asm__ volatile ("nop"); }
    __asm__ volatile ("rdtsc" : "=a"(lo2), "=d"(hi2));

    t1 = ((uint64_t)hi1 << 32) | lo1;
    t2 = ((uint64_t)hi2 << 32) | lo2;

    /* threshold: > 5 000 000 cycles ≈ single-stepping */
    return ((t2 - t1) > 5000000ULL);
#else
    return 0;
#endif
}

/* ------------------------------------------------------------------ */
/*  Decoy: outputs a convincing but wrong flag                        */
/* ------------------------------------------------------------------ */
static void print_decoy(void) {
    /* Looks like a real flag but is intentionally wrong */
    const char decoy[] = {
        0x66,0x6c,0x61,0x67,0x7b,0x66,0x34,0x6b,
        0x65,0x5f,0x64,0x65,0x62,0x75,0x67,0x67,
        0x65,0x72,0x5f,0x67,0x6f,0x74,0x5f,0x79,
        0x6f,0x75,0x7d,0x00
    };  /* flag{f4ke_debugger_got_you} */
    printf("[+] Key found: %s\n", decoy);
}

/* ------------------------------------------------------------------ */
/*  Real decryption: ROT-N with position-dependent shift              */
/* ------------------------------------------------------------------ */
static void decrypt_secret(const uint8_t *enc, size_t len, char *out) {
    for (size_t i = 0; i < len; i++) {
        /* shift = (i % 7) + 1, purely arithmetic, easy to invert */
        uint8_t shift = (uint8_t)((i % 7) + 1);
        out[i] = (char)((enc[i] - shift + 256) % 256);
    }
    out[len] = '\0';
}

/* ------------------------------------------------------------------ */
/*  Entry point                                                        */
/* ------------------------------------------------------------------ */
int main(void) {
    /* Build encrypted secret at runtime from compile-time flag */
    const char *flag   = FLAG_VALUE;
    size_t      flen   = strlen(flag);
    if (flen >= MAX_FLAG_LEN) flen = MAX_FLAG_LEN - 1;

    uint8_t secret_data[MAX_FLAG_LEN];
    for (size_t i = 0; i < flen; i++) {
        uint8_t shift  = (uint8_t)((i % 7) + 1);
        secret_data[i] = (uint8_t)((unsigned char)flag[i] + shift);
    }

    printf("==========================================\n");
    printf("  AntiDebug KeyGen v1.5 - Secure Edition  \n");
    printf("==========================================\n");

    /* Run all three anti-debug checks */
    int detected = ad_ptrace_check()
                 | ad_tracerpid_check()
                 | ad_timing_check();

    if (detected) {
        /* Under debugger: show decoy and exit */
        printf("[!] Environmental anomaly detected.\n");
        print_decoy();
        return EXIT_FAILURE;
    }

    /* Clean environment: show real flag */
    char result[MAX_FLAG_LEN + 1];
    decrypt_secret(secret_data, flen, result);
    printf("[+] Genuine key: %s\n", result);

    return EXIT_SUCCESS;
}
