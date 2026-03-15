/*
 * Challenge : Memory Integrity Checker
 * Type      : Reverse Engineering - XOR Encryption
 * Difficulty: Easy-Medium
 *
 * Description:
 *   A firmware integrity verification utility that checks an activation
 *   code against an XOR-encrypted reference stored in the .rodata section.
 *   The multi-round XOR key schedule is the only protection layer.
 *
 * Reversing approach:
 *   1. Locate `cipher_blob` in .rodata (static byte array)
 *   2. Identify the key derivation in `derive_round_key()`
 *   3. Replicate decryption: for each round, XOR with derived key
 *   4. The decrypted result is the flag
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#ifndef FLAG_VALUE
#define FLAG_VALUE "flag{placeholder_flag_value}"
#endif

#define MAX_FLAG_LEN  64
#define XOR_ROUNDS     4

/* ------------------------------------------------------------------ */
/*  Key schedule: each round key derived from base key + round index   */
/* ------------------------------------------------------------------ */
static void derive_round_key(uint8_t *key_out, size_t key_len,
                              uint8_t base, int round) {
    for (size_t i = 0; i < key_len; i++) {
        key_out[i] = (uint8_t)((base ^ (uint8_t)(round * 0x37)) + i) & 0xFF;
    }
}

/* ------------------------------------------------------------------ */
/*  Multi-round XOR encryption (symmetric: encrypt == decrypt)        */
/* ------------------------------------------------------------------ */
static void xor_transform(const uint8_t *in, uint8_t *out,
                           size_t len, uint8_t base_key) {
    uint8_t round_key[MAX_FLAG_LEN];

    /* copy input to output buffer first */
    memcpy(out, in, len);

    for (int r = 0; r < XOR_ROUNDS; r++) {
        derive_round_key(round_key, len, base_key, r);
        for (size_t i = 0; i < len; i++) {
            out[i] ^= round_key[i];
        }
    }
}

/* ------------------------------------------------------------------ */
/*  Build cipher blob at compile time (stored in .rodata)             */
/* ------------------------------------------------------------------ */
static void build_cipher_blob(uint8_t *blob, size_t *blob_len) {
    const char *flag = FLAG_VALUE;
    size_t      len  = strlen(flag);

    if (len >= MAX_FLAG_LEN) len = MAX_FLAG_LEN - 1;
    *blob_len = len;

    xor_transform((const uint8_t *)flag, blob, len, 0xA3);
}

/* ------------------------------------------------------------------ */
/*  Validation                                                         */
/* ------------------------------------------------------------------ */
static int validate_activation(const char *input) {
    static uint8_t cipher_blob[MAX_FLAG_LEN];
    static size_t  cipher_len = 0;
    static int     ready      = 0;

    if (!ready) {
        build_cipher_blob(cipher_blob, &cipher_len);
        ready = 1;
    }

    size_t input_len = strlen(input);
    if (input_len != cipher_len) return 0;

    /* encrypt the input with the same transform and compare */
    uint8_t encrypted_input[MAX_FLAG_LEN];
    xor_transform((const uint8_t *)input, encrypted_input, input_len, 0xA3);

    return (memcmp(encrypted_input, cipher_blob, cipher_len) == 0);
}

/* ------------------------------------------------------------------ */
/*  Entry point                                                        */
/* ------------------------------------------------------------------ */
int main(void) {
    char input[MAX_FLAG_LEN + 16];

    printf("=============================================\n");
    printf("  FirmwareGuard v3.0 - Activation Checker   \n");
    printf("=============================================\n");
    printf("Enter activation code: ");
    fflush(stdout);

    if (!fgets(input, sizeof(input), stdin)) {
        fprintf(stderr, "Read error.\n");
        return EXIT_FAILURE;
    }

    size_t len = strlen(input);
    if (len > 0 && input[len - 1] == '\n') input[--len] = '\0';

    if (len == 0) {
        printf("[-] Empty input. Exiting.\n");
        return EXIT_FAILURE;
    }

    if (validate_activation(input)) {
        printf("[+] Activation successful. Device unlocked.\n");
    } else {
        printf("[-] Invalid activation code. Remaining attempts logged.\n");
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
