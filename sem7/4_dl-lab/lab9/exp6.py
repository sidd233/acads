"""Experiment 6: PRE-ReLU versus POST-ReLU activation."""
from analysis import *

# ---- Experiment 6 ----
layer6, f6 = EXP6
post, pre = top_k(layer6, f6, "post"), top_k(layer6, f6, "pre")
zc = Z[layer6][:, f6 - 1].flatten(1).max(1).values
rows = ["| Rank | PRE idx | PRE digit | S_pre | PRE loc | POST idx | POST digit | S_post | POST loc |",
        "|---|---|---|---|---|---|---|---|---|"]
for r_, (a, b) in enumerate(zip(pre, post), 1):
    rows.append(f"| {r_} | {a['idx']} | {a['digit']} | {a['score']:.4f} | ({a['y']},{a['x']}) | "
                f"{b['idx']} | {b['digit']} | {b['score']:.4f} | ({b['y']},{b['x']}) |")
low_pre, low_post = top_k(layer6, f6, "pre", largest=False), top_k(layer6, f6, "post", largest=False)
low = ["", "Lowest-scoring images (least-negative PRE max is still negative; POST clamps to 0):",
       "| Rank from bottom | idx | digit | S_pre | S_post | loc of PRE max |", "|---|---|---|---|---|---|"]
for r_, (a, b) in enumerate(zip(low_pre, low_post), 1):
    low.append(f"| {r_} | {a['idx']} | {a['digit']} | {a['score']:.4f} | {max(a['score'], 0):.4f} | ({a['y']},{a['x']}) |")
same_set = {d['idx'] for d in pre} == {d['idx'] for d in post}
same_loc = all((a['y'], a['x']) == (b['y'], b['x']) for a, b in zip(pre, post) if a['idx'] == b['idx'])
neg = int((zc < 0).sum())
text = "\n".join([f"## Experiment 6: PRE vs POST-ReLU, {layer6} filter {f6}", "\n".join(rows), "",
       f"- Top-8 image sets identical: {same_set}; locations identical for shared images: {same_loc}",
       f"- Images whose PRE-ReLU maximum is negative (so S_post = 0): {neg} of {N_TEST}",
       f"- Min S_pre over all images: {zc.min():.4f}; Top-8 S_pre all positive: {all(d['score'] > 0 for d in pre)}",
       f"- Images with S_post = 0 (tied at zero): {int((torch.relu(zc) == 0).sum())}"] + low + [""])
(OUT / "exp6.md").write_text(text)
print(text)

