# Lab Test II: Smart Microwave Oven

**Microcontroller Design**
*(FSM + Interrupts + Timing + User Interaction)*
Department of Computer Science and Engineering 

---

## 1. Objective

The objective of this assignment is to design and simulate a microcontroller-based control system for a **Smart Microwave Oven**.

Students will learn:

* FSM-based control design
* Interrupt handling
* Timer-based execution
* Embedded system simulation

---

## 2. System Description

You are required to design a controller for a microwave oven.

### Inputs

* `START`
* `STOP`
* `DOOR CLOSED` (1 = closed, 0 = open)
* `FOOD PRESENT` (1 = present)
* `TEMP SENSOR` (1 = overheating)

### Outputs

* `HEATER` (ON/OFF)
* `TURNTABLE` (ON/OFF)
* `LIGHT` (ON/OFF)
* `BUZZER` (ON/OFF)
* `DISPLAY` (Mode + Time)

---

## 3. Operating Modes

| Mode    | Description  | Time (cycles) |
| ------- | ------------ | ------------- |
| DEFROST | Low power    | 3             |
| HEAT    | Medium power | 5             |
| GRILL   | High power   | 7             |

---

## 4. FSM States

```
IDLE → CHECK → RUN → PAUSE → COMPLETE → BUZZ → IDLE
                   ↓
                 ERROR
```

---

## 5. State Behavior

| State    | HEATER | TURNTABLE | LIGHT | BUZZER |
| -------- | ------ | --------- | ----- | ------ |
| IDLE     | OFF    | OFF       | OFF   | OFF    |
| CHECK    | OFF    | OFF       | ON    | OFF    |
| RUN      | ON     | ON        | ON    | OFF    |
| PAUSE    | OFF    | OFF       | ON    | OFF    |
| COMPLETE | OFF    | OFF       | ON    | OFF    |
| BUZZ     | OFF    | OFF       | OFF   | ON     |
| ERROR    | OFF    | OFF       | ON    | ON     |

---

## 6. Functional Rules

### Start Condition

System starts only if:

* `START = 1`
* `DOOR CLOSED = 1`
* `FOOD PRESENT = 1`

### Pause Condition

* `STOP` pressed → `PAUSE`
* Resume using `START`

### Completion

* When timer reaches zero → `COMPLETE → BUZZ`

---

## 7. Interrupt Handling

### Interrupt Priority

```
TEMP_SENSOR > DOOR_OPEN > STOP
```

### Interrupt Behavior

* `TEMP SENSOR = 1` → `ERROR` state immediately
* `DOOR CLOSED = 0` → `PAUSE` immediately

---

## 8. Timing Rules

* Each state = **1 cycle**
* RUN duration depends on selected mode
* Timer decreases every cycle in RUN

---

## 9. Display Requirement

At each cycle:

```
DISPLAY = MODE - Remaining Time
```

**Example:**

```
HEAT - 3
```

---

## 10. Execution Model

At each cycle:

1. Read inputs
2. Check interrupts
3. Execute state
4. Update outputs
5. Update timer
6. Print log

---

## 11. Output Format (Mandatory)

```
Cycle | State | Inputs | Outputs | Display
```

**Example:**

```
Cycle 3 | RUN | DOOR=1 | HEATER=ON | HEAT-3
```

---

## 12. Sample Test Cases

### Test Case 1: Normal Operation

* MODE = HEAT
* Cycle 1: `START=1, DOOR=1, FOOD=1`

**Expected Output (Key Steps):**

```
Cycle 2 | RUN | HEATER=ON | HEAT-5
Cycle 3 | RUN | HEAT-4
Cycle 7 | COMPLETE
Cycle 8 | BUZZ
```

---

### Test Case 2: Door Open During Run

* Cycle 4: `DOOR=0`

**Expected Output:**

```
Cycle 4 | PAUSE | HEATER=OFF
```

---

### Test Case 3: Resume

* Cycle 5: `START=1`

**Expected Output:**

```
Resume from remaining time
```

---

### Test Case 4: Overheat

* Cycle 3: `TEMP_SENSOR=1`

**Expected Output:**

```
Cycle 3 | ERROR | BUZZER=ON
```

---

### Test Case 5: Invalid Start

* `START=1, DOOR=0`

**Expected Output:**

```
System remains in IDLE
```

---

## 13. Tasks

* Draw microcontroller block diagram
* Draw FSM diagram
* Write C/C++ simulation
* Show outputs for all test cases

---

## 14. Important Notes

* Outputs depend only on **current state**
* Inputs may change during execution
* Exact cycle numbers may vary slightly, but logic must match
