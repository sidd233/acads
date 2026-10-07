## Experiment 5: receptive-field calculation
| Layer | k | s | r_l | j_l |
|---|---|---|---|---|
| Input | - | - | 1 | 1 |
| Conv1 | 5 | 1 | 5x5 | 1 |
| S2 AvgPool | 2 | 2 | 6x6 | 2 |
| Conv2 | 5 | 1 | 14x14 | 2 |
| S4 AvgPool | 2 | 2 | 16x16 | 4 |

| Layer | Neuron (y,x) | Theoretical RF | RF rows x cols | Visible in 28x28 |
|---|---|---|---|---|
| Conv1 | (0,0) | 5x5 | [0,4] x [0,4] | 5x5 |
| Conv1 | (12,12) | 5x5 | [12,16] x [12,16] | 5x5 |
| Conv1 | (23,23) | 5x5 | [23,27] x [23,27] | 5x5 |
| Conv2 | (0,0) | 14x14 | [0,13] x [0,13] | 14x14 |
| Conv2 | (4,4) | 14x14 | [8,21] x [8,21] | 14x14 |
| Conv2 | (7,7) | 14x14 | [14,27] x [14,27] | 14x14 |
