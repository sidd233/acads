"""Experiment 2: maximally activating images of one Conv1 filter (POST-ReLU)."""
from analysis import *

c1 = top_k("Conv1", EXP2_CONV1)
draw_top8("Conv1", EXP2_CONV1, c1, OUT / "fig1_conv1_top8.png",
          f"Conv1 filter {EXP2_CONV1}: Top-8 maximally activating test images (POST-ReLU)")
text = "\n".join([f"## Experiment 2: Conv1 filter {EXP2_CONV1}", detail("Conv1", EXP2_CONV1, c1), ""])
(OUT / "exp2.md").write_text(text)
print(text)
