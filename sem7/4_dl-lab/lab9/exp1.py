"""Experiment 1: train and verify the LeNet-style CNN."""
import json

import numpy as np
import torch
import torch.nn as nn

from common import CKPT, ROOT, SEED, LeNet, load_mnist, to_tensor

EPOCHS, BATCH, LR, MOM = 10, 64, 0.01, 0.9

torch.manual_seed(SEED)
np.random.seed(SEED)

# 60k train split -> 50k train / 10k validation; test = seeded 2000-image subset of the MNIST test split
x, y = load_mnist("train")
perm = np.random.RandomState(SEED).permutation(len(x))
tr, va = perm[:50000], perm[50000:]
xtr, ytr = to_tensor(x[tr]), torch.from_numpy(y[tr]).long()
xva, yva = to_tensor(x[va]), torch.from_numpy(y[va]).long()

from common import N_TEST
xt, yt = load_mnist("test")
te = np.random.RandomState(SEED).permutation(len(xt))[:N_TEST]
xte, yte = to_tensor(xt[te]), torch.from_numpy(yt[te]).long()

model = LeNet()
opt = torch.optim.SGD(model.parameters(), lr=LR, momentum=MOM)
loss_fn = nn.CrossEntropyLoss()


@torch.no_grad()
def evaluate(xs, ys):
    model.eval()
    out = model(xs)
    return loss_fn(out, ys).item(), (out.argmax(1) == ys).float().mean().item()


history = []
for ep in range(1, EPOCHS + 1):
    model.train()
    order = torch.randperm(len(xtr))
    tot_loss, correct = 0.0, 0
    for i in range(0, len(order), BATCH):
        idx = order[i:i + BATCH]
        out = model(xtr[idx])
        loss = loss_fn(out, ytr[idx])
        opt.zero_grad()
        loss.backward()
        opt.step()
        tot_loss += loss.item() * len(idx)
        correct += (out.argmax(1) == ytr[idx]).sum().item()
    vl, va_acc = evaluate(xva, yva)
    rec = dict(epoch=ep, train_loss=tot_loss / len(order), train_acc=correct / len(order),
               val_loss=vl, val_acc=va_acc)
    history.append(rec)
    print(f"epoch {ep:2d}  loss {rec['train_loss']:.4f}  train_acc {rec['train_acc']:.4f}  "
          f"val_acc {rec['val_acc']:.4f}")

_, test_acc = evaluate(xte, yte)
_, full_acc = evaluate(to_tensor(xt), torch.from_numpy(yt).long())
print(f"test accuracy ({N_TEST} images): {test_acc:.4f}   full 10k test: {full_acc:.4f}")
assert test_acc >= 0.97, "model must reach >= 97% test accuracy"

# output shape after every stage
model.eval()
shapes, h = [("Input", tuple(xte[:1].shape[1:]))], xte[:1]
for name, fn in [("Conv1", model.conv1), ("ReLU", torch.relu), ("AvgPool", model.pool),
                 ("Conv2", model.conv2), ("ReLU", torch.relu), ("AvgPool", model.pool),
                 ("Flatten", lambda t: t.flatten(1)), ("FC1", model.fc1), ("ReLU", torch.relu),
                 ("FC2", model.fc2), ("ReLU", torch.relu), ("FC3", model.fc3)]:
    h = fn(h)
    shapes.append((name, tuple(h.shape[1:])))
for n, s in shapes:
    print(f"{n:8s} {s}")

torch.save(model.state_dict(), CKPT)
(ROOT / "results").mkdir(exist_ok=True)
json.dump(dict(history=history, test_acc=test_acc, test_acc_full10k=full_acc, n_test=N_TEST,
               shapes=[(n, list(s)) for n, s in shapes]),
          open(ROOT / "results" / "exp1.json", "w"), indent=2)
