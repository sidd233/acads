import json
import time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from torchvision import datasets, transforms

NAME = "exp1"
SEED = 42
EPOCHS = 10
BATCH_SIZE = 64
LR = 0.001

# ---------------- data ----------------
# the same seed and the same indices are produced in every experiment file
tf = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
    transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616)),
])
train_full = datasets.ImageFolder("archive/CIFAR-10-images-master/train", transform=tf)
test_full = datasets.ImageFolder("archive/CIFAR-10-images-master/test", transform=tf)

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

g = torch.Generator()
g.manual_seed(SEED)
train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True, generator=g)
train_eval_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=False)
val_loader = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False)
test_loader = DataLoader(test_set, batch_size=BATCH_SIZE, shuffle=False)


# ---------------- model ----------------
class AlexNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 5, stride=1, padding=2), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 5, stride=1, padding=2), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(),
            nn.Conv2d(128, 128, 3, padding=1), nn.ReLU(),
            nn.Conv2d(128, 128, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(8192, 512), nn.ReLU(), nn.Dropout(0.5),
            nn.Linear(512, 256), nn.ReLU(), nn.Dropout(0.5),
            nn.Linear(256, 10),
        )

    def forward(self, x):
        return self.classifier(self.features(x))


torch.manual_seed(SEED)
model = AlexNet()
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=LR)
n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(NAME, "trainable parameters:", n_params)


# ---------------- train / evaluate ----------------
def evaluate(loader):
    model.eval()
    total_loss, correct, n = 0.0, 0, 0
    with torch.no_grad():
        for x, y in loader:
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
    start = time.time()
    for x, y in train_loader:
        optimizer.zero_grad()
        out = model(x)
        loss = criterion(out, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * x.size(0)
        correct += (out.argmax(1) == y).sum().item()
        n += x.size(0)
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

results = {
    "name": NAME,
    "params": n_params,
    "train_time_s": train_time,
    "history": history,
    "final_train_loss": final_train_loss,
    "final_train_acc": final_train_acc,
    "test_loss": test_loss,
    "test_acc": test_acc,
}
with open(f"{NAME}.json", "w") as f:
    json.dump(results, f, indent=2)
