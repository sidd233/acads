# Smart Washing Machine – Test Guide

---

## Compile & Run

```bash
# From the caa-lab/ directory
g++ -std=c++17 -Wall -o washing_machine main.cpp
./washing_machine
```

No external dependencies beyond `alu.hpp` (already in the same directory).

---

## Test Scenarios

### Worked Example (§11) — QUICK mode, all signals OK

**Setup inside `main.cpp`:**
```cpp
Mode  = QUICK
START = 1, DOOR = 1, WATER = 1, OVERLOAD = 0
No cycle events (no changes during run)
```

**Expected full output:**

```
Cycle 1  | LOCK   | … | LOCK=ON
Cycle 2  | LOCK   | … | LOCK=ON
Cycle 3  | FILL   | … | VALVE=ON  LOCK=ON
Cycle 4  | WASH   | … | MOTOR=ON  LOCK=ON
Cycle 5  | WASH   | … | MOTOR=ON  LOCK=ON
Cycle 6  | DRAIN  | … | LOCK=ON
Cycle 7  | UNLOCK | … | (all OFF)
Cycle 8  | UNLOCK | … | (all OFF)
Cycle 9  | BUZZ   | … | BUZZ=ON
>> Wash complete. Machine returned to IDLE.
```

**Verification checklist:**
- [ ] Cycles 1–2 are LOCK (2 cycles exactly)
- [ ] Cycle 3 is FILL (1 cycle because WATER=1 from start)
- [ ] Cycles 4–5 are WASH (2 cycles = QUICK mode)
- [ ] Cycle 6 is DRAIN (1 cycle)
- [ ] Cycles 7–8 are UNLOCK (2 cycles)
- [ ] Cycle 9 is BUZZ (1 cycle); simulation ends

---

### Test Case 1 — NORMAL mode, no faults

**Setup:**
```cpp
Mode  = NORMAL
START = 1, DOOR = 1, WATER = 1, OVERLOAD = 0
```

**Expected:**

```
Cycles 1–2  | LOCK
Cycle  3    | FILL
Cycles 4–7  | WASH   ← 4 cycles (NORMAL)
Cycle  8    | DRAIN
Cycles 9–10 | UNLOCK
Cycle  11   | BUZZ
>> Wash complete.
```

**Verification checklist:**
- [ ] WASH spans exactly 4 cycles (cycles 4, 5, 6, 7)
- [ ] Total run = 11 cycles

---

### Test Case 2 — Water delay

**Setup:**
```cpp
Mode  = NORMAL
START = 1, DOOR = 1, WATER = 0 initially
CycleEvent[5].water_ok = 1     ← water arrives at cycle 5
```

**Expected:**

```
Cycles 1–2  | LOCK
Cycles 3–5  | FILL   ← 3 cycles because WATER=0 until cycle 5
Cycles 6–9  | WASH   (4 cycles)
Cycle  10   | DRAIN
Cycles 11–12| UNLOCK
Cycle  13   | BUZZ
```

**Verification checklist:**
- [ ] FILL appears at cycles 3, 4, 5 (WATER=0 for the first two; WATER=1 at cycle 5 triggers exit)
- [ ] VALVE=ON only during FILL cycles, not during WASH
- [ ] Total run = 13 cycles (2 extra FILL cycles vs. Test 1)

---

### Test Case 3 — Door opens mid-wash

**Setup:**
```cpp
Mode  = NORMAL
START = 1, DOOR = 1, WATER = 1 initially
CycleEvent[4].door_closed = 0  ← door opens at cycle 4
```

**Expected:**

```
Cycles 1–2  | LOCK
Cycle  3    | FILL
Cycle  4    | ERROR   ← DOOR=0 detected; immediate interrupt
Cycle  5    | ERROR
Cycle  6    | ERROR
>> Machine halted in ERROR state.
```

**Verification checklist:**
- [ ] Cycle 4 shows `DOOR=0` in inputs
- [ ] State at cycle 4 is ERROR (not WASH — interrupt pre-empts the normal transition)
- [ ] ERROR outputs: MOTOR=OFF, VALVE=OFF, LOCK=ON, BUZZ=ON
- [ ] Machine never enters WASH state

---

### Test Case 4 — Overload mid-wash

**Setup:**
```cpp
Mode  = HEAVY
START = 1, DOOR = 1, WATER = 1 initially
CycleEvent[6].overload = 1     ← overload at cycle 6
```

**Expected:**

```
Cycles 1–2  | LOCK
Cycle  3    | FILL
Cycles 4–5  | WASH
Cycle  6    | ERROR   ← OVL=1 detected; immediate interrupt
Cycle  7    | ERROR
Cycle  8    | ERROR
>> Machine halted in ERROR state.
```

**Verification checklist:**
- [ ] Cycles 4–5 are WASH (interrupted before finishing 6 WASH cycles)
- [ ] Cycle 6 shows `OVL=1` and state = ERROR
- [ ] MOTOR turns OFF immediately at cycle 6

---

### Test Case 5 — HEAVY mode, full run

**Setup:**
```cpp
Mode  = HEAVY
START = 1, DOOR = 1, WATER = 1, OVERLOAD = 0
```

**Expected:**

```
Cycles 1–2   | LOCK
Cycle  3     | FILL
Cycles 4–9   | WASH   ← 6 cycles (HEAVY)
Cycle  10    | DRAIN
Cycles 11–12 | UNLOCK
Cycle  13    | BUZZ
>> Wash complete.
```

**Verification checklist:**
- [ ] WASH spans exactly 6 cycles (cycles 4–9)
- [ ] Total run = 13 cycles

---

### Test Case 6 — OVERLOAD + DOOR_OPEN simultaneously (priority test)

**Setup:**
```cpp
Mode  = QUICK
START = 1, DOOR = 1, WATER = 1 initially
CycleEvent[5].overload    = 1
CycleEvent[5].door_closed = 0   ← both faults at same cycle
```

**Expected:**

```
Cycles 1–2  | LOCK
Cycle  3    | FILL
Cycle  4    | WASH
Cycle  5    | ERROR   ← OVERLOAD wins (higher priority)
…
```

**Verification checklist:**
- [ ] ERROR is triggered at cycle 5 (not later)
- [ ] The interrupt encoder correctly prioritises OVERLOAD > DOOR_OPEN (no visible difference in output, but the code path branches on OVERLOAD first)

---

## Edge Cases to Check Manually

| Scenario | How to trigger | What to verify |
|---|---|---|
| FILL stays indefinitely | Set `water_ok = false`, add no `water_ok=1` event | FILL cycles keep printing with VALVE=ON |
| START pressed with door open | Set `door_closed = false` in initial inputs | Machine stays in IDLE (never enters LOCK) |
| Overload in LOCK state | `CycleEvent[1].overload = 1` | ERROR at cycle 1, never reaches FILL |
| Overload in UNLOCK state | Heavy mode + `CycleEvent[11].overload = 1` | ERROR during UNLOCK, wash unfinished |

To test these, edit the `simulate(...)` call arguments inside `main()` in `main.cpp` and recompile.

---

## Quick Reference: State Durations

| Mode   | LOCK | FILL | WASH | DRAIN | UNLOCK | BUZZ | Total (no delay) |
|--------|------|------|------|-------|--------|------|-----------------|
| QUICK  | 2    | ≥1   | 2    | 1     | 2      | 1    | 9+              |
| NORMAL | 2    | ≥1   | 4    | 1     | 2      | 1    | 11+             |
| HEAVY  | 2    | ≥1   | 6    | 1     | 2      | 1    | 13+             |
