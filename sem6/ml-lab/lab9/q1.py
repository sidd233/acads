import numpy as np
import matplotlib.pyplot as plt

np.random.seed(42)

# ── Dataset Generation ─────────────────────────────────────────────────────────
N = 800
x1 = np.random.uniform(-2, 2, N)
x2 = np.random.uniform(-2, 2, N)
eps = np.random.normal(0, 0.2, N)
z = np.sin(1.5 * x1) + x2**2 - 0.5 * x1 * x2 + eps
y = (z > 0).astype(float)

X = np.column_stack([x1, x2])   # (N, 2)
y = y.reshape(-1, 1)             # (N, 1)

# ── Train / Test Split (70 / 30) ───────────────────────────────────────────────
split = int(0.7 * N)
idx = np.random.permutation(N)
train_idx, test_idx = idx[:split], idx[split:]
X_train, y_train = X[train_idx], y[train_idx]
X_test,  y_test  = X[test_idx],  y[test_idx]

# ── MLP helpers ────────────────────────────────────────────────────────────────
def relu(z):        return np.maximum(0, z)
def relu_grad(z):   return (z > 0).astype(float)
def sigmoid(z):     return 1 / (1 + np.exp(-z))

def init_params(n_in, n_hidden):
    W1 = np.random.randn(n_in, n_hidden) * np.sqrt(2.0 / n_in)
    b1 = np.zeros((1, n_hidden))
    W2 = np.random.randn(n_hidden, 1) * np.sqrt(2.0 / n_hidden)
    b2 = np.zeros((1, 1))
    return W1, b1, W2, b2

def forward(X, W1, b1, W2, b2):
    Z1 = X @ W1 + b1
    A1 = relu(Z1)
    Z2 = A1 @ W2 + b2
    A2 = sigmoid(Z2)
    return Z1, A1, Z2, A2

def bce_loss(y_true, y_pred):
    clip = 1e-8
    return -np.mean(y_true * np.log(y_pred + clip) +
                    (1 - y_true) * np.log(1 - y_pred + clip))

def accuracy(y_true, y_pred):
    return np.mean((y_pred >= 0.5) == y_true)

def train_mlp(X_tr, y_tr, X_te, y_te, n_hidden, lr=0.01, epochs=120):
    W1, b1, W2, b2 = init_params(X_tr.shape[1], n_hidden)
    m = X_tr.shape[0]
    hist = {"train_loss": [], "test_loss": [], "train_acc": [], "test_acc": []}

    for _ in range(epochs):
        # Forward
        Z1, A1, _, A2 = forward(X_tr, W1, b1, W2, b2)

        # Backward
        dA2 = (A2 - y_tr) / m
        dW2 = A1.T @ dA2
        db2 = np.sum(dA2, axis=0, keepdims=True)
        dA1 = dA2 @ W2.T
        dZ1 = dA1 * relu_grad(Z1)
        dW1 = X_tr.T @ dZ1
        db1 = np.sum(dZ1, axis=0, keepdims=True)

        # Update
        W2 -= lr * dW2;  b2 -= lr * db2
        W1 -= lr * dW1;  b1 -= lr * db1

        # Metrics
        _, _, _, pred_tr = forward(X_tr, W1, b1, W2, b2)
        _, _, _, pred_te = forward(X_te, W1, b1, W2, b2)
        hist["train_loss"].append(bce_loss(y_tr, pred_tr))
        hist["test_loss"].append(bce_loss(y_te, pred_te))
        hist["train_acc"].append(accuracy(y_tr, pred_tr))
        hist["test_acc"].append(accuracy(y_te, pred_te))

    return hist

# ── Experiment ─────────────────────────────────────────────────────────────────
hidden_sizes = [2, 4, 8, 16, 32, 64]
results = {}

for h in hidden_sizes:
    print(f"Training h={h} ...", end=" ", flush=True)
    results[h] = train_mlp(X_train, y_train, X_test, y_test, n_hidden=h)
    print(f"done  |  final test acc = {results[h]['test_acc'][-1]:.4f}")

epochs_range = np.arange(1, 121)

# ── Plot 1: Loss curves for each h ─────────────────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
for ax, h in zip(axes.flatten(), hidden_sizes):
    ax.plot(epochs_range, results[h]["train_loss"], label="Train Loss", color="steelblue")
    ax.plot(epochs_range, results[h]["test_loss"],  label="Test Loss",  color="tomato", linestyle="--")
    ax.set_title(f"h = {h} neurons")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss (BCE)")
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.suptitle("Training vs Testing Loss – Different Hidden Layer Sizes", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("plots/q1_loss_curves.png", dpi=150)
plt.show()
print("Saved: plots/q1_loss_curves.png")

# ── Plot 2: Final accuracy vs hidden size ──────────────────────────────────────
final_train_acc = [results[h]["train_acc"][-1] for h in hidden_sizes]
final_test_acc  = [results[h]["test_acc"][-1]  for h in hidden_sizes]

plt.figure(figsize=(8, 5))
plt.plot(hidden_sizes, final_train_acc, marker="o", label="Train Accuracy", color="steelblue")
plt.plot(hidden_sizes, final_test_acc,  marker="s", label="Test Accuracy",  color="tomato", linestyle="--")
plt.xscale("log", base=2)
plt.xticks(hidden_sizes, labels=[str(h) for h in hidden_sizes])
plt.xlabel("Number of Hidden Neurons (h)")
plt.ylabel("Final Accuracy")
plt.title("Final Accuracy vs Hidden Layer Size")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("plots/q1_final_accuracy.png", dpi=150)
plt.show()
print("Saved: plots/q1_final_accuracy.png")
