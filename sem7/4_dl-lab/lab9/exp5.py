"""Experiment 5: mathematical receptive-field analysis."""
from analysis import *

# ---- Experiment 5 ----
sample = ["| Layer | Neuron (y,x) | Theoretical RF | RF rows x cols | Visible in 28x28 |", "|---|---|---|---|---|"]
for layer, pts in [("Conv1", [(0, 0), (12, 12), (23, 23)]), ("Conv2", [(0, 0), (4, 4), (7, 7)])]:
    for y, x in pts:
        t, l, sz, vis = rf_box(layer, y, x)
        sample.append(f"| {layer} | ({y},{x}) | {sz}x{sz} | [{t},{t + sz - 1}] x [{l},{l + sz - 1}] | {vis[0]}x{vis[1]} |")
text = "\n".join(["## Experiment 5: receptive-field calculation", "\n".join(rf_lines), "", "\n".join(sample), ""])
(OUT / "exp5.md").write_text(text)
print(text)

