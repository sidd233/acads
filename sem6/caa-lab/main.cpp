#include <cctype>
#include <cstdio>
#include <cstring>
#include <map>
#include <string>
#include "alu.hpp"

// fsm states
enum State : uint8_t {
    IDLE        = 0,
    LOCK        = 1,
    FILL        = 2,
    WASH        = 3,
    DRAIN       = 4,
    UNLOCK      = 5,
    BUZZ        = 6,
    ERROR_STATE = 7
};

// wash modes (value = required WASH cycles)
enum Mode : uint8_t {
    QUICK  = 2,
    NORMAL = 4,
    HEAVY  = 6
};

// i/o
struct Inputs {
    bool start       = false;
    bool door_closed = true;
    bool water_ok    = false;
    bool overload    = false;
};

struct Outputs {
    bool motor     = false;
    bool valve     = false;
    bool door_lock = false;
    bool buzzer    = false;
};

// Per-cycle input override; field = -1 means "no change this cycle"
struct CycleEvent {
    int start       = -1;
    int door_closed = -1;
    int water_ok    = -1;
    int overload    = -1;
};

// Pure combinational: state → outputs (Moore FSM)
static Outputs get_outputs(State s)
{
    Outputs o{};
    switch (s) {
        case LOCK:        o.door_lock = true;                        break;
        case FILL:        o.valve     = true; o.door_lock = true;    break;
        case WASH:        o.motor     = true; o.door_lock = true;    break;
        case DRAIN:       o.door_lock = true;                        break;
        case UNLOCK:      /* all outputs OFF */                       break;
        case BUZZ:        o.buzzer    = true;                        break;
        case ERROR_STATE: o.door_lock = true; o.buzzer = true;       break;
        default:          break;
    }
    return o;
}

// Helper

static const char* state_name(State s)
{
    switch (s) {
        case IDLE:        return "IDLE";
        case LOCK:        return "LOCK";
        case FILL:        return "FILL";
        case WASH:        return "WASH";
        case DRAIN:       return "DRAIN";
        case UNLOCK:      return "UNLOCK";
        case BUZZ:        return "BUZZ";
        case ERROR_STATE: return "ERROR";
    }
    return "???";
}

static const char* mode_name(Mode m)
{
    if (m == QUICK)  return "QUICK";
    if (m == NORMAL) return "NORMAL";
    return "HEAVY";
}

static void apply_events(Inputs& in, const std::map<int,CycleEvent>& ev, int cycle)
{
    auto it = ev.find(cycle);
    if (it == ev.end()) return;
    const CycleEvent& e = it->second;
    if (e.start       >= 0) in.start       = (bool)e.start;
    if (e.door_closed >= 0) in.door_closed = (bool)e.door_closed;
    if (e.water_ok    >= 0) in.water_ok    = (bool)e.water_ok;
    if (e.overload    >= 0) in.overload    = (bool)e.overload;
}

// Write separator line to file
static void write_sep(FILE* fp, int width = 88)
{
    for (int i = 0; i < width; ++i) fputc('-', fp);
    fputc('\n', fp);
}

// Write table header to file
static void write_header(FILE* fp)
{
    fprintf(fp, "%-8s | %-6s | %-32s | %s\n",
        "Cycle", "State", "Inputs", "Outputs");
    write_sep(fp);
}

// Write one cycle row to file
static void write_cycle(FILE* fp, int cycle, State s,
                         const Inputs& in, const Outputs& out)
{
    char ibuf[48], obuf[56];

    snprintf(ibuf, sizeof ibuf,
        "START=%d DOOR=%d WATER=%d OVL=%d",
        (int)in.start, (int)in.door_closed, (int)in.water_ok, (int)in.overload);

    snprintf(obuf, sizeof obuf,
        "MOTOR=%-3s VALVE=%-3s LOCK=%-3s BUZZ=%-3s",
        out.motor     ? "ON" : "OFF",
        out.valve     ? "ON" : "OFF",
        out.door_lock ? "ON" : "OFF",
        out.buzzer    ? "ON" : "OFF");

    fprintf(fp, "Cycle %-2d | %-6s | %-32s | %s\n",
        cycle, state_name(s), ibuf, obuf);
}

// Core Simulator
//
//  Execution model (per cycle, per spec §9):
//    1. Read inputs  (apply CycleEvent overrides)
//    2. Check interrupts (OVERLOAD > DOOR_OPEN; only in active non-ERROR states)
//    3. Execute current state (combinational output decode)
//    4. Update outputs  (written to file)
//    5. Transition to next state  (sequential logic, uses ALU for counters)
//

static void simulate(FILE*                           fp,
                     const char*                     label,
                     Mode                            mode,
                     Inputs                          initial_inputs,
                     const std::map<int,CycleEvent>& events,
                     int                             max_cycles = 60)
{
    fprintf(fp, "\n=== %-52s  [%s / %d wash-cycles] ===\n",
        label, mode_name(mode), (int)mode);
    write_header(fp);

    // Registers
    State   state_reg = IDLE;
    uint8_t cycle_ctr = 0;
    Inputs  in        = initial_inputs;

    // Pre-start: if START=1 and DOOR=1, enter LOCK immediately at cycle 1
    bool started = false;
    if (in.start && in.door_closed) {
        state_reg = LOCK;
        started   = true;
    }

    bool wash_complete = false;
    bool error_halt    = false;
    int  error_linger  = 0;

    for (int cycle = 1; cycle <= max_cycles; ++cycle) {

        // Step 1: Read inputs
        apply_events(in, events, cycle);

        // Handle late START (machine was sitting in IDLE)
        if (state_reg == IDLE && !started && in.start && in.door_closed) {
            state_reg = LOCK;
            started   = true;
            cycle_ctr = 0;
        }

        // Step 2: Interrupt check — priority: OVERLOAD > DOOR_OPEN
        // Only armed in active (non-IDLE, non-ERROR) states
        if (state_reg != IDLE && state_reg != ERROR_STATE) {
            if (in.overload) {
                state_reg    = ERROR_STATE;
                cycle_ctr    = 0;
                error_linger = 0;
            } else if (!in.door_closed) {
                state_reg    = ERROR_STATE;
                cycle_ctr    = 0;
                error_linger = 0;
            }
        }

        // Steps 3 & 4: Execute state → combinational output → write to file
        Outputs out = get_outputs(state_reg);
        write_cycle(fp, cycle, state_reg, in, out);

        // Step 5: Transition logic (ALU-based counters for timed states)
        switch (state_reg) {

            case IDLE:
                break;

            case LOCK: {
                ALUResult inc = alu_add(cycle_ctr, 1u);
                cycle_ctr = inc.value;
                ALUResult cmp = alu_cmp(cycle_ctr, 2u);
                if (cmp.Z) { state_reg = FILL; cycle_ctr = 0; }
                break;
            }

            case FILL:
                if (in.water_ok) { state_reg = WASH; cycle_ctr = 0; }
                break;

            case WASH: {
                ALUResult inc = alu_add(cycle_ctr, 1u);
                cycle_ctr = inc.value;
                ALUResult cmp = alu_cmp(cycle_ctr, static_cast<uint8_t>(mode));
                if (cmp.Z) { state_reg = DRAIN; cycle_ctr = 0; }
                break;
            }

            case DRAIN:
                state_reg = UNLOCK; cycle_ctr = 0;
                break;

            case UNLOCK: {
                ALUResult inc = alu_add(cycle_ctr, 1u);
                cycle_ctr = inc.value;
                ALUResult cmp = alu_cmp(cycle_ctr, 2u);
                if (cmp.Z) { state_reg = BUZZ; cycle_ctr = 0; }
                break;
            }

            case BUZZ:
                state_reg     = IDLE;
                cycle_ctr     = 0;
                started       = false;
                wash_complete = true;
                goto end_sim;

            case ERROR_STATE:
                if (++error_linger >= 3) { error_halt = true; goto end_sim; }
                break;
        }

        continue;
end_sim:
        break;
    }

    write_sep(fp);
    if (wash_complete) fprintf(fp, "  >> Wash complete. Machine returned to IDLE.\n");
    if (error_halt)    fprintf(fp, "  >> Machine halted in ERROR state (safety stop).\n");
}

// Interactive input helpers

// Read an integer in [lo, hi] from stdin; re-prompt on bad input
static int read_int(const char* prompt, int lo, int hi)
{
    int v;
    while (true) {
        printf("%s", prompt);
        fflush(stdout);
        if (scanf("%d", &v) == 1 && v >= lo && v <= hi) {
            // consume rest of line
            int c; while ((c = getchar()) != '\n' && c != EOF) {}
            return v;
        }
        // flush bad input
        int c; while ((c = getchar()) != '\n' && c != EOF) {}
        printf("  [!] Enter a number between %d and %d.\n", lo, hi);
    }
}

// Read a signal name, return index: 0=START 1=DOOR 2=WATER 3=OVERLOAD, -1=done
static int read_signal(const char* prompt)
{
    char buf[32];
    while (true) {
        printf("%s", prompt);
        fflush(stdout);
        if (scanf("%31s", buf) != 1) continue;
        // uppercase
        for (char* p = buf; *p; ++p) *p = (char)toupper((unsigned char)*p);
        if (!strcmp(buf, "START"))    return 0;
        if (!strcmp(buf, "DOOR"))     return 1;
        if (!strcmp(buf, "WATER"))    return 2;
        if (!strcmp(buf, "OVERLOAD")) return 3;
        if (!strcmp(buf, "OVL"))      return 3;
        if (!strcmp(buf, "DONE"))     return -1;
        printf("  [!] Valid signals: START  DOOR  WATER  OVERLOAD  (or DONE)\n");
    }
}

// Driver Code
int main()
{
    // Open trace file
    FILE* fp = fopen("cpu_trace.txt", "w");
    if (!fp) {
        fprintf(stderr, "Error: could not open cpu_trace.txt for writing.\n");
        return 1;
    }

    // Banner (terminal)
    printf("╔══════════════════════════════════════════════════════╗\n");
    printf("║       Smart Washing Machine FSM Simulator            ║\n");
    printf("╚══════════════════════════════════════════════════════╝\n\n");

    // Write banner to file
    fprintf(fp, "Smart Washing Machine FSM Simulator : CPU Trace\n");
    fprintf(fp, "CAA Lab | Cycle-by-Cycle Simulation\n");
    write_sep(fp);

    // Step 1: Choose wash mode
    printf("Select wash mode:\n");
    printf("  1. QUICK  (2 wash cycles)\n");
    printf("  2. NORMAL (4 wash cycles)\n");
    printf("  3. HEAVY  (6 wash cycles)\n");
    int mode_choice = read_int("Mode [1-3]: ", 1, 3);

    Mode mode;
    if      (mode_choice == 1) mode = QUICK;
    else if (mode_choice == 2) mode = NORMAL;
    else                       mode = HEAVY;

    // Step 2: Initial inputs
    printf("\nInitial inputs (0 or 1):\n");
    Inputs initial;
    initial.start       = (bool)read_int("  START       [0/1]: ", 0, 1);
    initial.door_closed = (bool)read_int("  DOOR_CLOSED [0/1]: ", 0, 1);
    initial.water_ok    = (bool)read_int("  WATER_OK    [0/1]: ", 0, 1);
    initial.overload    = (bool)read_int("  OVERLOAD    [0/1]: ", 0, 1);

    // Step 3: Per-cycle events
    std::map<int,CycleEvent> events;

    printf("\nPer-cycle input changes (type DONE as signal name to finish):\n");
    printf("  Signals: START  DOOR  WATER  OVERLOAD\n\n");

    while (true) {
        int cyc = read_int("  Cycle number (0 to finish): ", 0, 999);
        if (cyc == 0) break;

        int sig = read_signal("  Signal name: ");
        if (sig == -1) break;

        int val = read_int("  New value [0/1]: ", 0, 1);

        switch (sig) {
            case 0: events[cyc].start       = val; break;
            case 1: events[cyc].door_closed = val; break;
            case 2: events[cyc].water_ok    = val; break;
            case 3: events[cyc].overload    = val; break;
        }
        printf("  [+] Cycle %d: %s = %d\n\n",
            cyc,
            sig==0?"START":sig==1?"DOOR":sig==2?"WATER":"OVERLOAD",
            val);
    }

    // Step 4: Build label from user config
    char label[80];
    snprintf(label, sizeof label, "User simulation : %s mode", mode_name(mode));

    // Write config to file
    fprintf(fp, "\nConfiguration\n");
    fprintf(fp, "  Mode        : %s (%d wash cycles)\n", mode_name(mode), (int)mode);
    fprintf(fp, "  Initial     : START=%d DOOR=%d WATER=%d OVERLOAD=%d\n",
        (int)initial.start, (int)initial.door_closed,
        (int)initial.water_ok, (int)initial.overload);
    if (!events.empty()) {
        fprintf(fp, "  Cycle events:\n");
        for (auto& [cyc, e] : events) {
            if (e.start       >= 0) fprintf(fp, "    Cycle %d: START=%d\n",    cyc, e.start);
            if (e.door_closed >= 0) fprintf(fp, "    Cycle %d: DOOR=%d\n",     cyc, e.door_closed);
            if (e.water_ok    >= 0) fprintf(fp, "    Cycle %d: WATER=%d\n",    cyc, e.water_ok);
            if (e.overload    >= 0) fprintf(fp, "    Cycle %d: OVERLOAD=%d\n", cyc, e.overload);
        }
    }

    // Step 5: Run simulation
    simulate(fp, label, mode, initial, events);

    fclose(fp);

    printf("\nDone. Trace written to cpu_trace.txt\n");
    return 0;
}
