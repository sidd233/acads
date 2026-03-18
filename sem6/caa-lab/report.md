# Smart Washing Machine – Design Report

**CAA Lab | Microcontroller Design: FSM + Interrupts + Cycle-Based Simulation**

---

## 1. Architecture Overview

The simulator models a minimal synchronous microcontroller whose sole job is to
drive a washing machine.  It has no program memory or instruction fetch; instead
the control logic is hard-wired as a Moore FSM.  Every architectural block is
clocked by the same global cycle tick.

```
 ┌──────────────────────────────────────────────────────────────────┐
 │                     Washing Machine Microcontroller              │
 │                                                                  │
 │  Inputs                  Control Unit (FSM)          Outputs     │
 │  ────────               ──────────────────          ────────     │
 │  START    ──►  ┌─────────────────────────────────┐  ►  MOTOR     │
 │  DOOR     ──►  │  Interrupt   ┌───────────────┐  │  ►  VALVE     │
 │  WATER    ──►  │  Priority    │  State Reg    │  │  ►  DOOR_LOCK │
 │  OVERLOAD ──►  │  Encoder     │  (state_reg)  │  │  ►  BUZZER    │
 │                │     │        └───────┬───────┘  │               │
 │                │     ▼                │          │               │
 │                │  ┌──────────────┐    │          │               │
 │                │  │ Next-State   │◄───┘          │               │
 │                │  │ Logic        │               │               │
 │                │  └──────┬───────┘               │               │
 │                │         │                       │               │
 │                │  ┌──────▼───────┐               │               │
 │                │  │   ALU        │  cycle_ctr    │               │
 │                │  │  alu_add()   │◄──────────────┤               │
 │                │  │  alu_cmp()   │──────────────►│               │
 │                │  └──────────────┘               │               │
 │                └─────────────────────────────────┘               │
 └──────────────────────────────────────────────────────────────────┘
```

### Registers

| Register     | Width   | Purpose                                       |
|--------------|---------|-----------------------------------------------|
| `state_reg`  | 3 bits  | Encodes the current FSM state (8 states → 3 bits) |
| `cycle_ctr`  | 8 bits  | Counts cycles spent in timed states (ALU-managed) |
| `mode_reg`   | 8 bits  | Holds wash-duration target (2 / 4 / 6 cycles) |

### Combinational Logic Blocks

| Block                  | Function                                           |
|------------------------|----------------------------------------------------|
| Output decode          | `state_reg → {MOTOR, VALVE, DOOR_LOCK, BUZZER}` (Moore) |
| Interrupt priority enc.| `OVERLOAD > DOOR_OPEN > normal transition`         |
| Next-state logic       | FSM transition table; calls ALU for counter ops    |

### ALU Usage

The ALU from `alu.hpp` provides gate-level arithmetic rather than using native
C++ operators, faithfully modelling hardware:

| Operation        | Call         | Used in state |
|------------------|--------------|---------------|
| Increment counter | `alu_add(cycle_ctr, 1)` | LOCK, WASH, UNLOCK |
| Compare to target | `alu_cmp(cycle_ctr, N)` | LOCK (N=2), WASH (N=mode), UNLOCK (N=2) |

The `Z` (zero) flag returned by `alu_cmp` drives the state transition – exactly
as a hardware comparator drives a branch condition.

---

## 2. FSM Design

### 2.1 State Table

| State   | Entry condition                               | Exit condition                          |
|---------|-----------------------------------------------|-----------------------------------------|
| IDLE    | Reset / after BUZZ completes                  | START=1 ∧ DOOR=1 → LOCK                |
| LOCK    | From IDLE                                     | cycle_ctr reaches 2 → FILL             |
| FILL    | From LOCK                                     | WATER=1 → WASH                         |
| WASH    | From FILL                                     | cycle_ctr reaches mode target → DRAIN  |
| DRAIN   | From WASH                                     | (1 cycle) → UNLOCK                     |
| UNLOCK  | From DRAIN                                    | cycle_ctr reaches 2 → BUZZ             |
| BUZZ    | From UNLOCK                                   | (1 cycle) → IDLE                       |
| ERROR   | From any active state via interrupt           | stays in ERROR (safety hold)            |

### 2.2 Output Truth Table (Moore — outputs depend only on state)

| State   | MOTOR | VALVE | DOOR_LOCK | BUZZER |
|---------|-------|-------|-----------|--------|
| IDLE    | OFF   | OFF   | OFF       | OFF    |
| LOCK    | OFF   | OFF   | ON        | OFF    |
| FILL    | OFF   | ON    | ON        | OFF    |
| WASH    | ON    | OFF   | ON        | OFF    |
| DRAIN   | OFF   | OFF   | ON        | OFF    |
| UNLOCK  | OFF   | OFF   | OFF       | OFF    |
| BUZZ    | OFF   | OFF   | OFF       | ON     |
| ERROR   | OFF   | OFF   | ON        | ON     |

*Rationale:* The door stays locked (DOOR_LOCK=ON) during all phases where water
or mechanical motion is present (LOCK through DRAIN).  UNLOCK deliberately turns
the lock OFF for two cycles to give the solenoid time to disengage.  ERROR keeps
the door locked for safety but sounds the buzzer to alert the user.

### 2.3 FSM Diagram (ASCII)

```
                          ┌──────────────────────────────────────────┐
           Interrupt:     │  OVERLOAD=1  or  DOOR_CLOSED=0           │
           (any active    │  (checked every cycle, highest priority) │
            state)        └──────────────┬───────────────────────────┘
                                         ▼
  [START=1,DOOR=1]                  ┌─────────┐
  ┌───────────────────────────────► │  ERROR  │ ◄── stays here
  │                                 └─────────┘      (safety hold)
  │
  │     LOCK          FILL         WASH
  │   ┌──────┐  c=2  ┌──────┐ W=1 ┌──────┐ c=mode
  ▼   │      │──────►│      │────►│      │──────────────┐
[IDLE]│ 2cyc │       │ ≥1cy │     │ 2/4/6│              │
  ▲   └──────┘       └──────┘     └──────┘              ▼
  │                                                 ┌──────┐
  │ [BUZZ done]            ┌──────┐   ┌──────┐  1cy │DRAIN │
  └────────────────────────│ BUZZ │◄──│UNLOCK│◄─────└──────┘
                           │ 1cyc │   │ 2cyc │
                           └──────┘   └──────┘
```

### 2.4 Timing

| State  | Duration                                |
|--------|-----------------------------------------|
| LOCK   | 2 cycles (counted by ALU)               |
| FILL   | Variable: 1 cycle minimum, stays until WATER=1 |
| WASH   | QUICK=2 / NORMAL=4 / HEAVY=6 (counted by ALU) |
| DRAIN  | 1 cycle                                 |
| UNLOCK | 2 cycles (counted by ALU)               |
| BUZZ   | 1 cycle                                 |

---

## 3. Interrupt Logic

### 3.1 Priority Encoder

```
if (OVERLOAD == 1)         → ERROR   [highest priority]
else if (DOOR_CLOSED == 0) → ERROR   [second priority]
else                       → normal FSM transition
```

The priority encoder is checked **at the beginning of every non-IDLE, non-ERROR
cycle**, before any state logic executes.  This models an asynchronous interrupt
that pre-empts the current instruction.

### 3.2 Why interrupts are masked in IDLE

IDLE represents the unpowered / standby condition.  There is no motor running,
no water valve open, and no door lock engaged.  Triggering ERROR in IDLE would
be meaningless (nothing to stop) and could confuse the user if a sensor glitches
at power-on.  Interrupts are therefore only armed once the machine has entered
LOCK (i.e., the user has pressed START with the door closed).

### 3.3 ERROR State Semantics

ERROR is a **safety hold**: all actuators are off except the door lock (user
cannot open the door while water may still be inside) and the buzzer (alerts the
user).  The machine does **not** self-recover; a hardware reset (power cycle) is
required to return to IDLE.  This matches real-world washing machine behaviour
for safety-critical faults.

### 3.4 Interrupt Timing

```
Cycle N:
  ① Read inputs  ← OVERLOAD becomes 1 here
  ② Interrupt check → state_reg := ERROR, cycle_ctr := 0   [pre-empts state]
  ③ Execute ERROR  → DOOR_LOCK=ON, BUZZER=ON
  ④ Output ERROR signals
  ⑤ No transition (stays in ERROR)
```

The interrupt takes effect in the **same cycle** it is detected—zero latency—
because steps ①–② both happen before step ③ (state execution).

---

## 4. Cycle Execution Model

The per-cycle pipeline (§9 of the spec) maps to the simulator as follows:

```
┌─────────────────────────────────────────────────────────────────┐
│  Each Clock Cycle                                               │
│                                                                 │
│  Step 1: apply_events()       — new input values latch in       │
│  Step 2: interrupt_check()    — OVERLOAD / DOOR_OPEN → ERROR    │
│  Step 3: get_outputs()        — combinational decode            │
│  Step 4: print_cycle()        — record & display outputs        │
│  Step 5: next_state_logic()   — ALU counters + FSM transitions  │
└─────────────────────────────────────────────────────────────────┘
```

State changes take effect at the **end** of the cycle (step 5), so the printed
output always reflects the state that was active during that cycle's execution.

---

## 5. Design Decisions and Trade-offs

### Moore vs. Mealy FSM

A **Moore FSM** was chosen: outputs depend only on the current state, not on
inputs.  This prevents glitchy output behaviour if an input changes mid-cycle
(e.g., a noisy WATER sensor pulse would not momentarily start the motor).

### Synchronous Interrupts

Interrupts are checked once per cycle (synchronous), not asynchronously.  This
keeps the simulation deterministic and cycle-accurate.  In real hardware you
would typically use a level-triggered interrupt with a priority encoder before
the FSM's next-state logic—which is exactly what the code models.

### ALU for Control

Using `alu_add` and `alu_cmp` from `alu.hpp` for cycle counting may seem
over-engineered for software, but it faithfully models what the hardware ALU
does: the control unit re-uses the datapath ALU to compare the cycle counter
against the target duration, returning a Z-flag that drives the branch condition.
This is a classic RISC microcontroller pattern.

### FILL Minimum Duration

FILL has no fixed duration—it waits for an external signal (WATER_LEVEL_OK).
In the implementation the transition check happens at the **end** of the FILL
cycle (step 5), so FILL always executes at least one full cycle even if WATER=1
at entry.  This ensures the valve solenoid gets at least one cycle of drive
current before the state is left.

---

## 6. Worked Example Trace (QUICK mode)

```
Pre-start: START=1, DOOR=1 → IDLE → LOCK immediately (cycle 1)

Cycle 1 | LOCK   | cycle_ctr=0 → alu_add→1 → alu_cmp(1,2): Z=0 → stay LOCK
Cycle 2 | LOCK   | cycle_ctr=1 → alu_add→2 → alu_cmp(2,2): Z=1 → FILL
Cycle 3 | FILL   | WATER=1 → transition to WASH
Cycle 4 | WASH   | cycle_ctr=0 → alu_add→1 → alu_cmp(1,2): Z=0 → stay WASH
Cycle 5 | WASH   | cycle_ctr=1 → alu_add→2 → alu_cmp(2,2): Z=1 → DRAIN
Cycle 6 | DRAIN  | 1 cycle → UNLOCK
Cycle 7 | UNLOCK | cycle_ctr=0 → 1 → cmp(1,2)=0 → stay
Cycle 8 | UNLOCK | cycle_ctr=1 → 2 → cmp(2,2)=1 → BUZZ
Cycle 9 | BUZZ   | 1 cycle → IDLE (wash complete)
```

Total: **9 cycles** for QUICK mode with no delays or faults.

---

## 7. Summary

| Component       | Implementation                                     |
|-----------------|----------------------------------------------------|
| Architecture    | Synchronous Moore FSM microcontroller              |
| Registers       | `state_reg` (3-bit), `cycle_ctr` (8-bit), `mode_reg` |
| ALU             | `alu_add` + `alu_cmp` from `alu.hpp` for counters  |
| Interrupt logic | Priority encoder: OVERLOAD > DOOR_OPEN → ERROR     |
| Output logic    | Combinational decode of state only (Moore)         |
| Timing          | All signals synchronous; state changes end-of-cycle |
