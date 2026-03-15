/*
 * Challenge : Serial Key Validator
 * Type      : Reverse Engineering - String Comparison
 * Difficulty: Easy
 *
 * Description:
 *   A license key validation program. The correct key is derived from
 *   a multi-stage transformation of the embedded flag.
 *   Reverse the transformation logic to recover the original flag.
 *
 * Reversing approach:
 *   1. strings / IDA / Ghidra: locate the encoded key buffer
 *   2. Trace validate_key() to understand the encoding scheme
 *   3. Invert the transformation: sub 3, XOR 0x5A, reverse → flag
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Build system injects the real flag via -DFLAG_VALUE="flag{...}" */
#ifndef FLAG_VALUE
#define FLAG_VALUE "flag{placeholder_flag_value}"
#endif

#define MAX_KEY_LEN 128

/* ------------------------------------------------------------------ */
/*  Encoding: each byte = (original ^ 0x5A) + 3, then string reversed */
/* ------------------------------------------------------------------ */
static void encode_flag(const char *flag, char *out, size_t out_sz) {
    size_t len = strlen(flag);
    if (len >= out_sz) len = out_sz - 1;

    for (size_t i = 0; i < len; i++) {
        out[i] = (char)(((unsigned char)flag[i] ^ 0x5A) + 3);
    }
    out[len] = '\0';

    /* reverse in-place */
    for (size_t i = 0, j = len - 1; i < j; i++, j--) {
        char tmp = out[i];
        out[i]   = out[j];
        out[j]   = tmp;
    }
}

/* ------------------------------------------------------------------ */
/*  Validation: encode user input and compare with stored key          */
/* ------------------------------------------------------------------ */
static int validate_key(const char *input) {
    static char stored_key[MAX_KEY_LEN];
    static int  initialized = 0;

    if (!initialized) {
        encode_flag(FLAG_VALUE, stored_key, sizeof(stored_key));
        initialized = 1;
    }

    char encoded_input[MAX_KEY_LEN];
    encode_flag(input, encoded_input, sizeof(encoded_input));

    return (strcmp(encoded_input, stored_key) == 0);
}

/* ------------------------------------------------------------------ */
/*  Entry point                                                        */
/* ------------------------------------------------------------------ */
int main(void) {
    char input[MAX_KEY_LEN];

    printf("========================================\n");
    printf("   SecureApp v2.1 - License Validator   \n");
    printf("========================================\n");
    printf("Please enter your license key: ");
    fflush(stdout);

    if (!fgets(input, sizeof(input), stdin)) {
        fprintf(stderr, "Input error.\n");
        return EXIT_FAILURE;
    }

    /* strip trailing newline */
    size_t len = strlen(input);
    if (len > 0 && input[len - 1] == '\n') input[--len] = '\0';

    if (len == 0) {
        printf("[-] No input provided. Exiting.\n");
        return EXIT_FAILURE;
    }

    if (validate_key(input)) {
        printf("[+] License key accepted! Welcome.\n");
        printf("[+] Authenticated as: %s\n", input);
    } else {
        printf("[-] Invalid license key. Access denied.\n");
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
