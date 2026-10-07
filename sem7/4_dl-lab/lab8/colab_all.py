import time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader, TensorDataset
from torchvision import datasets, transforms

SEED = 42
EPOCHS = 10
BATCH_SIZE = 64
LR = 0.001
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("device:", device)

# ---------------- data (same split for every experiment) ----------------
tf = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
    transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616)),
])
train_full = datasets.CIFAR10("data", train=True, download=True, transform=tf)
test_full = datasets.CIFAR10("data", train=False, download=True, transform=tf)

rng = np.random.RandomState(SEED)
perm = rng.permutation(len(train_full))
train_idx = perm[:12000]
val_idx = perm[12000:14000]
test_idx = rng.permutation(len(test_full))[:2000]


def to_tensors(ds, idx):
    # transform once up front so the epochs do not redo the resizing
    x = torch.stack([ds[i][0] for i in idx])
    y = torch.tensor([ds[i][1] for i in idx])
    return TensorDataset(x, y)


train_set = to_tensors(train_full, train_idx)
val_set = to_tensors(train_full, val_idx)
test_set = to_tensors(test_full, test_idx)
val_loader = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False)
test_loader = DataLoader(test_set, batch_size=BATCH_SIZE, shuffle=False)
train_eval_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=False)


# ---------------- model ----------------
class AlexNet(nn.Module):
    def __init__(self, ch, fc1, fc2):
        # ch = [conv1, conv2, conv3, conv4, conv5] output channels
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, ch[0], 5, stride=1, padding=2), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(ch[0], ch[1], 5, stride=1, padding=2), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(ch[1], ch[2], 3, padding=1), nn.ReLU(),
            nn.Conv2d(ch[2], ch[3], 3, padding=1), nn.ReLU(),
            nn.Conv2d(ch[3], ch[4], 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(ch[4] * 8 * 8, fc1), nn.ReLU(), nn.Dropout(0.5),
            nn.Linear(fc1, fc2), nn.ReLU(), nn.Dropout(0.5),
            nn.Linear(fc2, 10),
        )

    def forward(self, x):
        return self.classifier(self.features(x))


experiments = {
    "exp1": ("Baseline", [32, 64, 128, 128, 128], 512, 256),
    "exp2": ("Reduced classifier", [32, 64, 128, 128, 128], 256, 128),
    "exp3": ("Reduced width", [16, 32, 64, 64, 64], 512, 256),
}


def sync():
    if device.type == "cuda":
        torch.cuda.synchronize()


def run(key):
    label, ch, fc1, fc2 = experiments[key]
    # fresh seed and a fresh shuffling generator for every experiment
    torch.manual_seed(SEED)
    model = AlexNet(ch, fc1, fc2).to(device)
    g = torch.Generator()
    g.manual_seed(SEED)
    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True, generator=g)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n{label}: {n_params:,} trainable parameters")

    def evaluate(loader):
        model.eval()
        total_loss, correct, n = 0.0, 0, 0
        with torch.no_grad():
            for x, y in loader:
                x, y = x.to(device), y.to(device)
                out = model(x)
                total_loss += criterion(out, y).item() * x.size(0)
                correct += (out.argmax(1) == y).sum().item()
                n += x.size(0)
        return total_loss / n, correct / n

    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}
    train_time = 0.0
    for epoch in range(EPOCHS):
        model.train()
        total_loss, correct, n = 0.0, 0, 0
        sync()
        start = time.time()
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * x.size(0)
            correct += (out.argmax(1) == y).sum().item()
            n += x.size(0)
        sync()
        train_time += time.time() - start

        val_loss, val_acc = evaluate(val_loader)
        history["train_loss"].append(total_loss / n)
        history["train_acc"].append(correct / n)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        print(f"epoch {epoch + 1:2d} | train loss {total_loss / n:.4f} acc {correct / n:.4f}"
              f" | val loss {val_loss:.4f} acc {val_acc:.4f}")

    # final numbers with dropout off, and the one and only look at the test set
    final_train_loss, final_train_acc = evaluate(train_eval_loader)
    test_loss, test_acc = evaluate(test_loader)
    print(f"train time {train_time:.1f}s | eval-mode train acc {final_train_acc:.4f}"
          f" | test acc {test_acc:.4f}")
    return {"label": label, "params": n_params, "train_time_s": train_time,
            "history": history, "final_train_loss": final_train_loss,
            "final_train_acc": final_train_acc, "test_loss": test_loss, "test_acc": test_acc}


res = {k: run(k) for k in experiments}

# ---------------- consolidated table ----------------
rows = []
for k, r in res.items():
    h = r["history"]
    rows.append({
        "Model": r["label"],
        "Train acc (%)": 100 * r["final_train_acc"],
        "Val acc (%)": 100 * h["val_acc"][-1],
        "Test acc (%)": 100 * r["test_acc"],
        "Train loss": r["final_train_loss"],
        "Val loss": h["val_loss"][-1],
        "Gap (pts)": 100 * (r["final_train_acc"] - h["val_acc"][-1]),
        "Params": r["params"],
        "Time (s)": r["train_time_s"],
    })
df = pd.DataFrame(rows).round(3)
print("\n", df.to_string(index=False))
df.to_csv("results_table.csv", index=False)

# ---------------- plots ----------------
colors = {"exp1": "tab:blue", "exp2": "tab:orange", "exp3": "tab:green"}
epochs = range(1, EPOCHS + 1)

for fname, tr, va, ylabel in [("plot_accuracy.png", "train_acc", "val_acc", "Accuracy"),
                              ("plot_loss.png", "train_loss", "val_loss", "Cross-entropy loss")]:
    plt.figure(figsize=(6, 4))
    for k, r in res.items():
        plt.plot(epochs, r["history"][tr], "--", color=colors[k], label=r["label"] + " (train)")
        plt.plot(epochs, r["history"][va], "-", color=colors[k], label=r["label"] + " (val)")
    plt.xlabel("Epoch")
    plt.ylabel(ylabel)
    plt.legend(fontsize=7)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(fname, dpi=200)
    plt.show()

plt.figure(figsize=(6, 4))
for k, r in res.items():
    x, y = r["params"] / 1e6, 100 * r["history"]["val_acc"][-1]
    plt.scatter(x, y, color=colors[k], s=60)
    plt.annotate(r["label"], (x, y), textcoords="offset points", xytext=(6, 6), fontsize=8)
plt.xlabel("Trainable parameters (millions)")
plt.ylabel("Final validation accuracy (%)")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("plot_params.png", dpi=200)
plt.show()
