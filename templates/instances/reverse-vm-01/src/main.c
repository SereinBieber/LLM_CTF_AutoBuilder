/*
 * Challenge : MiniVM Flag Checker
 * Type      : Reverse Engineering - Custom Virtual Machine
 * Difficulty: Hard
 *
 * Description:
 *   A compact register-based virtual machine executes a bytecode program
 *   that validates user input character-by-character.
 *   The bytecode is embedded as a static array; reversing the ISA and
 *   disassembling the program reveals the expected input (the flag).
 *
 * VM Architecture:
 *   - 8 general-purpose 32-bit registers: R0–R7
 *   - R7 is the program counter (PC), R6 is used as accumulator
 *   - 256-byte addressable memory (heap)
 *   - Instruction word: 32 bits  [opcode:8 | dst:4 | src_a:4 | imm:16]
 *
 * Instruction Set:
 *   0x01  LOAD_IMM  dst, imm       → R[dst] = imm
 *   0x02  LOAD_MEM  dst, src_a     → R[dst] = mem[R[src_a]]
 *   0x03  STORE_MEM dst, src_a     → mem[R[dst]] = R[src_a]
 *   0x04  ADD       dst, src_a     → R[dst] += R[src_a]
 *   0x05  XOR       dst, src_a     → R[dst] ^= R[src_a]
 *   0x06  CMP_EQ    dst, src_a     → R[dst] = (R[dst] == R[src_a]) ? 1 : 0
 *   0x07  JMP_IF    dst, imm       → if R[dst] == 0: PC += imm (relative)
 *   0x08  HALT                     → stop execution
 *   0x09  IN        dst            → R[dst] = next byte from input buffer
 *   0x0A  OUT       src_a          → output R[src_a] to result register
 *
 * Reversing approach:
 *   1. Identify the bytecode array `vm_program[]`
 *   2. Write a disassembler for the 10-instruction ISA
 *   3. Trace the CMP_EQ / JMP_IF chain to extract expected byte values
 *   4. Concatenate expected bytes → flag
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#ifndef FLAG_VALUE
#define FLAG_VALUE "flag{placeholder_flag_value}"
#endif

#define VM_MEM_SIZE   256
#define VM_REG_COUNT  8
#define VM_PC_REG     7
#define MAX_CYCLES    65536

/* ------------------------------------------------------------------ */
/*  VM state                                                           */
/* ------------------------------------------------------------------ */
typedef struct {
    uint32_t reg[VM_REG_COUNT];
    uint8_t  mem[VM_MEM_SIZE];
    int      halted;
    int      pass;           /* set to 1 when all checks pass */
    /* input stream */
    const uint8_t *input;
    size_t         input_pos;
    size_t         input_len;
} VM;

/* ------------------------------------------------------------------ */
/*  Instruction decode                                                 */
/* ------------------------------------------------------------------ */
typedef struct {
    uint8_t  opcode;
    uint8_t  dst;
    uint8_t  src_a;
    uint16_t imm;
} Instr;

static Instr decode(uint32_t word) {
    Instr i;
    i.opcode = (word >> 24) & 0xFF;
    i.dst    = (word >> 20) & 0x0F;
    i.src_a  = (word >> 16) & 0x0F;
    i.imm    = (word)       & 0xFFFF;
    return i;
}

/* ------------------------------------------------------------------ */
/*  Execute one instruction                                            */
/* ------------------------------------------------------------------ */
static void vm_step(VM *vm, const uint32_t *program, size_t prog_len) {
    uint32_t pc = vm->reg[VM_PC_REG];
    if (pc >= (uint32_t)prog_len) { vm->halted = 1; return; }

    Instr ins = decode(program[pc]);
    vm->reg[VM_PC_REG]++;   /* default: advance PC */

    switch (ins.opcode) {
    case 0x01: /* LOAD_IMM */
        vm->reg[ins.dst] = ins.imm;
        break;
    case 0x02: /* LOAD_MEM */
        vm->reg[ins.dst] = vm->mem[vm->reg[ins.src_a] & (VM_MEM_SIZE - 1)];
        break;
    case 0x03: /* STORE_MEM */
        vm->mem[vm->reg[ins.dst] & (VM_MEM_SIZE - 1)] = (uint8_t)vm->reg[ins.src_a];
        break;
    case 0x04: /* ADD */
        vm->reg[ins.dst] += vm->reg[ins.src_a];
        break;
    case 0x05: /* XOR */
        vm->reg[ins.dst] ^= vm->reg[ins.src_a];
        break;
    case 0x06: /* CMP_EQ */
        vm->reg[ins.dst] = (vm->reg[ins.dst] == vm->reg[ins.src_a]) ? 1 : 0;
        break;
    case 0x07: /* JMP_IF: relative jump if R[dst] == 0 */
        if (vm->reg[ins.dst] == 0) {
            /* imm is signed relative offset */
            vm->reg[VM_PC_REG] = (uint32_t)((int32_t)pc + (int16_t)ins.imm + 1);
        }
        break;
    case 0x08: /* HALT */
        vm->halted = 1;
        break;
    case 0x09: /* IN */
        if (vm->input_pos < vm->input_len) {
            vm->reg[ins.dst] = vm->input[vm->input_pos++];
        } else {
            vm->reg[ins.dst] = 0;
        }
        break;
    case 0x0A: /* OUT: treat as "accept" signal */
        vm->pass = (int)vm->reg[ins.src_a];
        break;
    default:
        /* unknown opcode → halt */
        vm->halted = 1;
        break;
    }
}

/* ------------------------------------------------------------------ */
/*  Bytecode compiler: generate a checker program for `flag`          */
/*                                                                     */
/*  Generated program per character at index i:                       */
/*    IN  R0               ; read input byte                          */
/*    LOAD_IMM R1, flag[i] ; load expected byte                       */
/*    CMP_EQ R0, R1        ; R0 = (R0 == R1)                         */
/*    JMP_IF R0, +2        ; if R0 == 0 → jump to FAIL               */
/*    (continue to next char)                                         */
/*  After all chars:                                                   */
/*    LOAD_IMM R2, 1       ; success                                  */
/*    OUT R2                                                           */
/*    HALT                                                             */
/*  FAIL:                                                              */
/*    LOAD_IMM R2, 0                                                   */
/*    OUT R2                                                           */
/*    HALT                                                             */
/* ------------------------------------------------------------------ */
#define EMIT(arr, idx, word)  (arr)[(idx)++] = (word)
#define PACK(op,d,s,i) ( ((uint32_t)(op)<<24) | ((uint32_t)(d)<<20) \
                       | ((uint32_t)(s)<<16) | ((uint32_t)(i)&0xFFFF) )

static size_t compile_checker(const char *flag, uint32_t *prog, size_t max_words) {
    size_t   flen = strlen(flag);
    size_t   pc   = 0;
    /* Each character: 4 instructions. Tail: 6 instructions. */
    if (pc + flen * 4 + 6 > max_words) return 0;

    for (size_t i = 0; i < flen; i++) {
        uint8_t expected = (uint8_t)flag[i];
        /* IN R0 */
        EMIT(prog, pc, PACK(0x09, 0, 0, 0));
        /* LOAD_IMM R1, expected */
        EMIT(prog, pc, PACK(0x01, 1, 0, expected));
        /* CMP_EQ R0, R1 */
        EMIT(prog, pc, PACK(0x06, 0, 1, 0));
        /* JMP_IF R0, relative: jump to FAIL block
         * remaining chars * 4 instructions + 2 success instructions ahead
         * offset = remaining_chars*4 + 2  (will land on FAIL LOAD_IMM) */
        uint16_t offset = (uint16_t)((flen - i - 1) * 4 + 2);
        EMIT(prog, pc, PACK(0x07, 0, 0, offset));
    }

    /* SUCCESS path */
    EMIT(prog, pc, PACK(0x01, 2, 0, 1));   /* LOAD_IMM R2, 1 */
    EMIT(prog, pc, PACK(0x0A, 0, 2, 0));   /* OUT R2          */
    EMIT(prog, pc, PACK(0x08, 0, 0, 0));   /* HALT            */

    /* FAIL path */
    EMIT(prog, pc, PACK(0x01, 2, 0, 0));   /* LOAD_IMM R2, 0 */
    EMIT(prog, pc, PACK(0x0A, 0, 2, 0));   /* OUT R2          */
    EMIT(prog, pc, PACK(0x08, 0, 0, 0));   /* HALT            */

    return pc;
}

/* ------------------------------------------------------------------ */
/*  Entry point                                                        */
/* ------------------------------------------------------------------ */
int main(void) {
    char input[128];

    printf("============================================\n");
    printf("   MiniVM Integrity Checker v0.9-beta       \n");
    printf("============================================\n");
    printf("Enter passphrase: ");
    fflush(stdout);

    if (!fgets(input, sizeof(input), stdin)) {
        fprintf(stderr, "Read error.\n");
        return EXIT_FAILURE;
    }
    size_t ilen = strlen(input);
    if (ilen > 0 && input[ilen - 1] == '\n') input[--ilen] = '\0';

    /* Compile flag into bytecode at runtime */
    uint32_t vm_program[1024];
    size_t   prog_len = compile_checker(FLAG_VALUE, vm_program,
                                        sizeof(vm_program) / sizeof(vm_program[0]));
    if (prog_len == 0) {
        fprintf(stderr, "Bytecode compilation failed.\n");
        return EXIT_FAILURE;
    }

    /* Run VM */
    VM vm;
    memset(&vm, 0, sizeof(vm));
    vm.input     = (const uint8_t *)input;
    vm.input_len = ilen;

    int cycles = 0;
    while (!vm.halted && cycles < MAX_CYCLES) {
        vm_step(&vm, vm_program, prog_len);
        cycles++;
    }

    if (vm.pass) {
        printf("[+] Passphrase accepted. Access granted.\n");
    } else {
        printf("[-] Incorrect passphrase.\n");
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
