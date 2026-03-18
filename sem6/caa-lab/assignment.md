# Lab Test: Smart Washing Machine

**Microcontroller Design (FSM + Interrupts + Cycle-Based Simulation)**
Department of Computer Science and Engineering

---

## 1. Objective

This test evaluates your ability to:

* Design a microcontroller architecture
* Model control logic using FSM
* Handle interrupts
* Perform cycle-by-cycle simulation

---

## 2. System Description

### Inputs

* START
* DOOR CLOSED (1 = closed, 0 = open)
* WATER LEVEL OK (1 = sufficient water)
* OVERLOAD (1 = overload condition)

### Outputs

* MOTOR (ON/OFF)
* VALVE (ON/OFF)
* DOOR LOCK (ON/OFF)
* BUZZER (ON/OFF)

---

## 3. Operating Modes

| Mode   | Wash Duration (cycles) |
| ------ | ---------------------- |
| QUICK  | 2                      |
| NORMAL | 4                      |
| HEAVY  | 6                      |

---

## 4. FSM States and Meaning

| State  | Description                         |
| ------ | ----------------------------------- |
| IDLE   | Waiting for START                   |
| LOCK   | Lock door (2 cycles)                |
| FILL   | Fill water until WATER LEVEL OK = 1 |
| WASH   | Motor ON for required cycles        |
| DRAIN  | Stop water/motor                    |
| UNLOCK | Unlock door (2 cycles)              |
| BUZZ   | Indicate completion                 |
| ERROR  | Safety stop state                   |

---

## 5. State Output Behavior

| State  | MOTOR | VALVE | DOOR LOCK | BUZZER |
| ------ | ----- | ----- | --------- | ------ |
| LOCK   | OFF   | OFF   | ON        | OFF    |
| FILL   | OFF   | ON    | ON        | OFF    |
| WASH   | ON    | OFF   | ON        | OFF    |
| DRAIN  | OFF   | OFF   | ON        | OFF    |
| UNLOCK | OFF   | OFF   | OFF       | OFF    |
| BUZZ   | OFF   | OFF   | OFF       | ON     |
| ERROR  | OFF   | OFF   | ON        | ON     |

---

## 6. Timing Rules

* Each state takes **1 cycle** unless specified
* **LOCK and UNLOCK take 2 cycles**
* **WASH duration depends on mode**
* State changes occur at the **end of each cycle**

---

## 7. Interrupt Handling

### Priority Order

```
OVERLOAD > DOOR_OPEN > NORMAL TRANSITION
```

### Behavior

* OVERLOAD = 1 → go to **ERROR immediately**
* DOOR CLOSED = 0 → go to **ERROR immediately**
* Interrupt overrides all states

---

## 8. Input Behavior

Inputs may change during execution.

Example:

* Cycle 3: WATER_LEVEL_OK becomes 1
* Cycle 5: OVERLOAD becomes 1

You must read inputs **at every cycle**

---

## 9. Execution Model (Step-by-Step)

At each cycle:

1. Read inputs
2. Check interrupts
3. Execute current state
4. Update outputs
5. Transition to next state

---

## 10. Output Format (Mandatory)

```
Cycle | State | Inputs | Outputs
```

Example:

```
Cycle 3 | FILL | W=0 | VALVE=ON
```

---

## 11. Worked Example

**MODE = QUICK**

**Cycle 1 Inputs:**
START=1, DOOR=1, WATER=1

### Execution

```
Cycle 1 | LOCK  | DOOR_LOCK=ON
Cycle 2 | LOCK  | DOOR_LOCK=ON
Cycle 3 | FILL  | VALVE=ON
Cycle 4 | WASH  | MOTOR=ON
Cycle 5 | WASH  | MOTOR=ON
Cycle 6 | DRAIN | MOTOR=OFF
```

---

## 12. Sample Test Cases

### Test Case 1 (Normal)

**MODE = NORMAL**

Cycle 1: START=1, DOOR=1, WATER=1

**Expected:**

```
Cycle 4–7 | WASH | MOTOR=ON
Cycle 8   | DRAIN
```

---

### Test Case 2 (Water Delay)

* Cycle 1: WATER=0
* Cycle 3: WATER=1

**Expected:**

* FILL continues until WATER=1
* Then transition to WASH

---

### Test Case 3 (Door Interrupt)

* Cycle 4: DOOR=0

**Expected:**

* Immediate transition to ERROR
* MOTOR=OFF, BUZZER=ON

---

### Test Case 4 (Overload)

* Cycle 6: OVERLOAD=1

**Expected:**

* Immediate ERROR state

---

## 13. Tasks

* Draw architecture diagram
* Draw FSM diagram
* Write C/C++ simulator
* Print cycle-by-cycle output

---

## 14. Evaluation

| Component       | Marks   |
| --------------- | ------- |
| Architecture    | 20      |
| FSM             | 20      |
| Interrupt Logic | 20      |
| Simulation Code | 20      |
| Output          | 10      |
| Viva            | 10      |
| **Total**       | **100** |

---

## 15. Important Assumptions

* All signals are **synchronous per cycle**
* Only one state is active at a time
* Outputs depend only on current state

