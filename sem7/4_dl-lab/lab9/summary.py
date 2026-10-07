"""Builds the consolidated results table and merges the per-experiment results into results/results.md."""
from analysis import *

sel_rows = [("Conv1", f) for f in EXP4_CONV1] + [("Conv2", f) for f in EXP4_CONV2]
tab = ["| Layer | Filter | Activation mode | Top-1 digit | Top-1 activation | Top-1 location | RF size | Top-8 digit distribution |",
       "|---|---|---|---|---|---|---|---|"]
for layer, f in [("Conv1", EXP2_CONV1), ("Conv2", EXP3_CONV2)] + sel_rows:
    it = top_k(layer, f)
    tab.append(f"| {layer} | {f} | POST-ReLU | {it[0]['digit']} | {it[0]['score']:.4f} | "
               f"({it[0]['y']},{it[0]['x']}) | {RF_SIZE[layer]}x{RF_SIZE[layer]} | {dist(it)} |")
parts = ["# Consolidated results", "\n".join(tab), ""]
parts += [(OUT / f"exp{n}.md").read_text() for n in (2, 3, 4, 5, 6)]
(OUT / "results.md").write_text("\n".join(parts))
print("\n".join(parts))
