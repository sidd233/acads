/*
Mini-RISC Processor - Assignment VI Final Version
Includes:
- 2-bit predictor
- Speculation + recovery
- Timer interrupts
- Exceptions
- Command-line program input
- Full execution trace to cpu_trace.txt
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MEM_SIZE 256
#define BP_SIZE 16
#define TIMER_PERIOD 20
#define INT_HANDLER 200

#define OP_NOP 0x0
#define OP_LOAD 0x1
#define OP_STORE 0x2
#define OP_MOVI 0x3
#define OP_ADD 0x4
#define OP_SUB 0x5
#define OP_DIV 0x7
#define OP_CMP 0x9
#define OP_JMP 0xA
#define OP_JZ 0xB
#define OP_IRET 0xE
#define OP_HALT 0xF

typedef struct
{
    unsigned char R[4];
    unsigned char ACC;
    unsigned char PC;
    unsigned char Z, C;

    unsigned char EPC;
    unsigned char CAUSE;
    unsigned char IE;
} CPU;

typedef struct
{
    unsigned char IR;
    unsigned char PC;
    int valid;
    int predicted_taken;
} IFEX;

typedef struct
{
    int valid;
    int counter;
} BPEntry;

CPU cpu;
IFEX ifex;
BPEntry bp_table[BP_SIZE];
unsigned char IMEM[MEM_SIZE];

int cycles = 0;
int instructions = 0;
int total_branches = 0;
int mispredictions = 0;
int branch_penalty_cycles = 0;
int interrupts = 0;
int exceptions = 0;

FILE *trace_fp;

/* ================= RESET ================= */

void reset_cpu()
{
    memset(&cpu, 0, sizeof(cpu));
    memset(&ifex, 0, sizeof(ifex));
    memset(bp_table, 0, sizeof(bp_table));
    memset(IMEM, 0, sizeof(IMEM));
    cpu.IE = 1;
}

/* ================= PROGRAM LOAD ================= */

void load_program(const char *file)
{
    FILE *fp = fopen(file, "r");
    if (!fp)
    {
        printf("Error: Cannot open program file %s\n", file);
        exit(1);
    }

    unsigned int x;
    int i = 0;

    while (fscanf(fp, "%x", &x) != EOF)
    {
        if (i >= MEM_SIZE)
        {
            printf("Error: Program too large.\n");
            fclose(fp);
            exit(1);
        }
        IMEM[i++] = (unsigned char)x;
    }

    fclose(fp);
}

/* ================= TRACE ================= */

void log_trace()
{
    fprintf(trace_fp,
            "Cycle:%3d PC:%3d ACC:%3d Z:%d IE:%d INST:%02X\n",
            cycles, cpu.PC, cpu.ACC, cpu.Z, cpu.IE,
            ifex.valid ? ifex.IR : 0xFF);
}

/* ================= BRANCH PREDICTOR ================= */

int bp_index(unsigned char pc) { return pc % BP_SIZE; }

int predict_branch(unsigned char pc)
{
    int idx = bp_index(pc);
    if (!bp_table[idx].valid)
        return 0;
    return (bp_table[idx].counter >= 2);
}

void update_predictor(unsigned char pc, int taken)
{
    int idx = bp_index(pc);
    bp_table[idx].valid = 1;
    if (taken && bp_table[idx].counter < 3)
        bp_table[idx].counter++;
    else if (!taken && bp_table[idx].counter > 0)
        bp_table[idx].counter--;
}

/* ================= INTERRUPTS ================= */

int interrupt_pending()
{
    return (cpu.IE && cycles % TIMER_PERIOD == 0);
}

void raise_interrupt(int cause)
{
    cpu.EPC = cpu.PC;
    cpu.CAUSE = cause;
    cpu.IE = 0;
    ifex.valid = 0;
    cpu.PC = INT_HANDLER;
    interrupts++;
}

/* ================= EXCEPTIONS ================= */

void raise_exception(int cause)
{

    cpu.EPC = ifex.PC;
    cpu.CAUSE = cause;
    cpu.IE = 0;
    ifex.valid = 0;

    exceptions++;

    printf("\n=== EXCEPTION OCCURRED ===\n");
    printf("Cause code : %d\n", cause);
    printf("Faulting PC: %d\n", cpu.EPC);

    fprintf(trace_fp, "\n=== EXCEPTION OCCURRED ===\n");
    fprintf(trace_fp, "Cause code : %d\n", cause);
    fprintf(trace_fp, "Faulting PC: %d\n", cpu.EPC);

    printf("\n==== FINAL REPORT ====\n");
    printf("Instructions          : %d\n", instructions);
    printf("Branches              : %d\n", total_branches);
    printf("Mispredictions        : %d\n", mispredictions);
    printf("Interrupts            : %d\n", interrupts);
    printf("Exceptions            : %d\n", exceptions);
    printf("Total cycles          : %d\n", cycles);
    printf("CPI                   : %.2f\n",
           (float)cycles / instructions);

    fclose(trace_fp);
    exit(0);
}

/* ================= FETCH ================= */

void fetch_stage()
{

    if (ifex.valid)
        return;

    ifex.IR = IMEM[cpu.PC];
    ifex.PC = cpu.PC;
    ifex.valid = 1;

    unsigned char op = (ifex.IR >> 4) & 0xF;

    if (op == OP_JMP || op == OP_JZ)
    {
        int pred = predict_branch(cpu.PC);
        ifex.predicted_taken = pred;
        cpu.PC = pred ? (ifex.IR & 0xF) : cpu.PC + 1;
    }
    else
    {
        ifex.predicted_taken = 0;
        cpu.PC++;
    }
}

/* ================= EXECUTE ================= */

void execute_stage()
{

    if (!ifex.valid)
        return;

    unsigned char ir = ifex.IR;
    unsigned char op = (ir >> 4) & 0xF;
    unsigned char arg = ir & 0xF;

    instructions++;

    switch (op)
    {

    case OP_MOVI:
        cpu.ACC = arg;
        break;
    case OP_LOAD:
        cpu.ACC = cpu.R[arg];
        break;
    case OP_STORE:
        cpu.R[arg] = cpu.ACC;
        break;
    case OP_ADD:
        cpu.ACC += cpu.R[arg];
        break;
    case OP_SUB:
        cpu.ACC -= cpu.R[arg];
        break;

    case OP_DIV:
        if (cpu.R[arg] == 0)
        {
            raise_exception(1);
            return;
        }
        cpu.ACC /= cpu.R[arg];
        break;

    case OP_CMP:
        cpu.Z = (cpu.ACC == cpu.R[arg]);
        break;

    case OP_JMP:
    case OP_JZ:
    {
        total_branches++;
        int actual = (op == OP_JMP) ? 1 : cpu.Z;
        int predicted = ifex.predicted_taken;

        if (actual != predicted)
        {
            mispredictions++;
            branch_penalty_cycles += 2;
            cpu.PC = actual ? arg : (ifex.PC + 1);
            ifex.valid = 0;
        }

        update_predictor(ifex.PC, actual);
        break;
    }

    case OP_IRET:
        cpu.PC = cpu.EPC;
        cpu.IE = 1;
        break;

    case OP_HALT:
        printf("\n==== FINAL REPORT ====\n");
        printf("Instructions          : %d\n", instructions);
        printf("Branches              : %d\n", total_branches);
        printf("Mispredictions        : %d\n", mispredictions);
        printf("Branch penalty cycles : %d\n", branch_penalty_cycles);
        printf("Interrupts            : %d\n", interrupts);
        printf("Exceptions            : %d\n", exceptions);
        printf("Total cycles          : %d\n", cycles);
        printf("CPI                   : %.2f\n",
               (float)cycles / instructions);

        fprintf(trace_fp, "\n==== FINAL REPORT ====\n");
        fprintf(trace_fp, "Instructions:%d\n", instructions);
        fprintf(trace_fp, "Branches:%d\n", total_branches);
        fprintf(trace_fp, "Mispredictions:%d\n", mispredictions);
        fprintf(trace_fp, "Interrupts:%d\n", interrupts);
        fprintf(trace_fp, "Exceptions:%d\n", exceptions);
        fprintf(trace_fp, "Cycles:%d\n", cycles);

        fclose(trace_fp);
        exit(0);

    default:
        raise_exception(2);
        return;
    }

    ifex.valid = 0;
}

/* ================= MAIN ================= */

int main(int argc, char *argv[])
{

    if (argc != 2)
    {
        printf("Usage: %s <program.hex>\n", argv[0]);
        return 1;
    }

    trace_fp = fopen("cpu_trace.txt", "w");
    if (!trace_fp)
    {
        printf("Error: Cannot create cpu_trace.txt\n");
        return 1;
    }

    reset_cpu();
    load_program(argv[1]);

    while (1)
    {
        cycles++;

        execute_stage();

        if (interrupt_pending())
        {
            raise_interrupt(0);
            continue;
        }

        fetch_stage();
        log_trace();
    }

    return 0;
}
