"""Experiment 3: Conv2 filter Top-8, to compare with Conv1 (Experiment 2)."""
from analysis import *

c2 = top_k("Conv2", EXP3_CONV2)
draw_top8("Conv2", EXP3_CONV2, c2, OUT / "fig2_conv2_top8.png",
          f"Conv2 filter {EXP3_CONV2}: Top-8 maximally activating test images and RFs (POST-ReLU)")
text = "\n".join([f"## Experiment 3: Conv2 filter {EXP3_CONV2}", detail("Conv2", EXP3_CONV2, c2), ""])
(OUT / "exp3.md").write_text(text)
print(text)
