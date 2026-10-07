"""Shared helpers for Experiments 2-6: scoring, Top-8 search, receptive fields, plotting."""
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from matplotlib.patches import Rectangle

from common import CKPT, N_TEST, ROOT, SEED, LeNet, load_mnist, to_tensor

# No filters were assigned, so these are fixed, documented choices (1-indexed).
EXP2_CONV1 = 2
EXP3_CONV2 = 7
EXP4_CONV1 = [1, 3, 5]
EXP4_CONV2 = [5, 10, 14]
EXP6 = ("Conv2", 3)
K = 8
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

model = LeNet()
model.load_state_dict(torch.load(CKPT))
model.eval()

xt, yt = load_mnist("test")
sel = np.random.RandomState(SEED).permutation(len(xt))[:N_TEST]
imgs, labels = xt[sel], yt[sel]
with torch.no_grad():
    Z1, Z2 = model.feature_maps(to_tensor(imgs))
Z = {"Conv1": Z1, "Conv2": Z2}  # PRE-ReLU, shapes (N,6,24,24) / (N,16,8,8)

# ---- receptive field geometry (Experiment 5) ----
# layer: (kernel, stride); r_l = r_{l-1} + (k-1)*j_{l-1}; j_l = j_{l-1}*s
LAYERS = [("Conv1", 5, 1), ("S2 AvgPool", 2, 2), ("Conv2", 5, 1), ("S4 AvgPool", 2, 2)]
RF_SIZE = {}
rf_lines = ["| Layer | k | s | r_l | j_l |", "|---|---|---|---|---|", "| Input | - | - | 1 | 1 |"]
r, j = 1, 1
for name, k, s in LAYERS:
    r = r + (k - 1) * j
    j = j * s
    RF_SIZE[name.split()[0]] = r if name in ("Conv1", "Conv2") else RF_SIZE.get(name.split()[0])
    rf_lines.append(f"| {name} | {k} | {s} | {r}x{r} | {j} |")
    if name in ("Conv1", "Conv2"):
        RF_SIZE[name] = r
assert (RF_SIZE["Conv1"], RF_SIZE["Conv2"]) == (5, 14)
STRIDE = {"Conv1": 1, "Conv2": 2}  # input-pixel offset per feature-map step (jump at that layer's input)


def rf_box(layer, y, x):
    """Theoretical RF in input coords: (top, left, size), plus its visible part in 28x28."""
    s, sz = STRIDE[layer], RF_SIZE[layer]
    t, l = y * s, x * s
    vt, vl = max(t, 0), max(l, 0)
    vb, vr = min(t + sz, 28), min(l + sz, 28)
    return t, l, sz, (vb - vt, vr - vl)


def top_k(layer, f, mode="post", k=K, largest=True):
    z = Z[layer][:, f - 1]
    a = torch.relu(z) if mode == "post" else z
    flat = a.flatten(1)
    score, pos = flat.max(1)  # S_i and argmax per image
    order = torch.argsort(score, descending=largest, stable=True)[:k]
    w = a.shape[-1]
    out = []
    for i in order.tolist():
        y, x = divmod(pos[i].item(), w)
        out.append(dict(idx=i, digit=int(labels[i]), score=score[i].item(), y=y, x=x,
                        rf=rf_box(layer, y, x)))
    return out


def crop(i, rf):
    t, l, sz, _ = rf
    img = np.pad(imgs[i], sz)  # pad so partially-outside RFs still crop; not needed here but safe
    return img[t + sz:t + 2 * sz, l + sz:l + 2 * sz]


def dist(items):
    c = Counter(d["digit"] for d in items)
    return ", ".join(f"{d}:{n}" for d, n in sorted(c.items(), key=lambda t: (-t[1], t[0])))


def classify(items):
    c = Counter(d["digit"] for d in items)
    top = max(c.values())
    if top >= 6:
        return "class-associated"
    if len(c) >= 3:
        return "multi-class"
    return "unclassified (2 classes, none >=6)"


def draw_top8(layer, f, items, path, title):
    fig, ax = plt.subplots(2, K, figsize=(2 * K, 4.8))
    for c, d in enumerate(items):
        t, l, sz, vis = d["rf"]
        a = ax[0, c]
        a.imshow(imgs[d["idx"]], cmap="gray", vmin=0, vmax=255)
        a.add_patch(Rectangle((l - .5, t - .5), sz, sz, fill=False, ec="red", lw=1.5))
        cy, cx = t + (sz - 1) / 2, l + (sz - 1) / 2  # centre of the RF = location in input space
        a.plot(cx, cy, "c+", ms=8, mew=1.5)
        a.set_title(f"#{c + 1} digit {d['digit']}\nA={d['score']:.2f} @({d['y']},{d['x']})", fontsize=8)
        a.axis("off")
        b = ax[1, c]
        b.imshow(crop(d["idx"], d["rf"]), cmap="gray", vmin=0, vmax=255)
        b.set_title(f"RF crop {sz}x{sz}", fontsize=8)
        b.axis("off")
    fig.suptitle(title + "\nred box = theoretical RF, cyan + = RF centre of the max-response neuron; "
                 "(y,x) = feature-map location", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def detail(layer, f, items):
    rows = ["| Rank | Test idx | Digit | S (POST) | Location (y,x) | RF region (rows, cols) | Visible RF |",
            "|---|---|---|---|---|---|---|"]
    for r_, d in enumerate(items, 1):
        t, l, sz, vis = d["rf"]
        rows.append(f"| {r_} | {d['idx']} | {d['digit']} | {d['score']:.4f} | ({d['y']},{d['x']}) | "
                    f"[{t},{t + sz - 1}] x [{l},{l + sz - 1}] | {vis[0]}x{vis[1]} |")
    return "\n".join(rows)


