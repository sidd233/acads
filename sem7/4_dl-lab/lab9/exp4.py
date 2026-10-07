"""Experiment 4: filter selectivity across digit classes."""
from analysis import *

# ---- Experiment 4 ----
sel_rows = [("Conv1", f) for f in EXP4_CONV1] + [("Conv2", f) for f in EXP4_CONV2]
fig, ax = plt.subplots(len(sel_rows), K, figsize=(1.7 * K, 2.1 * len(sel_rows)))
ex4 = ["## Experiment 4: selectivity", "| Layer | Filter | Digits (rank order) | Activations | Distribution | Class |",
       "|---|---|---|---|---|---|"]
for r_, (layer, f) in enumerate(sel_rows):
    items = top_k(layer, f)
    for c, d in enumerate(items):
        ax[r_, c].imshow(crop(d["idx"], d["rf"]), cmap="gray", vmin=0, vmax=255)
        ax[r_, c].set_title(f"{d['digit']}  A={d['score']:.2f}", fontsize=7)
        ax[r_, c].set_xticks([]); ax[r_, c].set_yticks([])
    ax[r_, 0].set_ylabel(f"{layer} f{f}\n{classify(items)}", fontsize=7)
    ex4.append(f"| {layer} | {f} | {' '.join(str(d['digit']) for d in items)} | "
               f"{', '.join(f'{d['score']:.2f}' for d in items)} | {dist(items)} | {classify(items)} |")
fig.suptitle("Filter selectivity: RF crops of the Top-8 images (POST-ReLU); title = digit, activation", fontsize=10)
fig.tight_layout()
fig.savefig(OUT / "fig3_selectivity.png", dpi=140)
plt.close(fig)
text = "\n".join(ex4 + [""])
(OUT / "exp4.md").write_text(text)
print(text)

