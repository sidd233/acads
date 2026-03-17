import numpy as np
import matplotlib.pyplot as plt

# ── Reproducibility ────────────────────────────────────────────────────────────
np.random.seed(42)

# ── Dataset (same as Q1) ───────────────────────────────────────────────────────
N = 800
x1 = np.random.uniform(-2, 2, N)
x2 = np.random.uniform(-2, 2, N)
eps = np.random.normal(0, 0.2, N)
z = np.sin(1.5 * x1) + x2**2 - 0.5 * x1 * x2 + eps
y = (z > 0).astype(float).reshape(-1, 1)
X = np.column_stack([x1, x2])

split = int(0.7 * N)
idx = np.random.permutation(N)
X_train, y_train = X[idx[:split]], y[idx[:split]]
X_test,  y_test  = X[idx[split:]], y[idx[split:]]

# ── Activation functions ───────────────────────────────────────────────────────
def relu(z):      return np.maximum(0, z)
def relu_d(z):    return (z > 0).astype(float)
def sigmoid(z):   return 1 / (1 + np.exp(-z))

# ── Generic multi-layer MLP ────────────────────────────────────────────────────
def init_weights(layer_sizes):
    params = []
    for i in range(len(layer_sizes) - 1):
        n_in, n_out = layer_sizes[i], layer_sizes[i + 1]
        W = np.random.randn(n_in, n_out) * np.sqrt(2.0 / n_in)
        b = np.zeros((1, n_out))
        params.append((W, b))
    return params

def forward(X, params):
    cache = [X]
    A = X
    for i, (W, b) in enumerate(params):
        Z = A @ W + b
        if i < len(params) - 1:   # hidden layers → ReLU
            A = relu(Z)
        else:                       # output layer → Sigmoid
            A = sigmoid(Z)
        cache.append((Z, A))
    return cache

def bce_loss(y_true, y_pred):
    clip = 1e-8
    return -np.mean(y_true * np.log(y_pred + clip) +
                    (1 - y_true) * np.log(1 - y_pred + clip))

def accuracy(y_true, y_pred):
    return np.mean((y_pred >= 0.5) == y_true)

def backward_and_update(cache, params, y_true, lr):
    m = y_true.shape[0]
    L = len(params)

    # output layer gradient (BCE + sigmoid combined)
    _, A_out = cache[-1]
    dA = (A_out - y_true) / m

    for i in reversed(range(L)):
        Z_i, A_i = cache[i + 1]
        A_prev = cache[i] if i == 0 else cache[i][1]

        dW = A_prev.T @ dA
        db = np.sum(dA, axis=0, keepdims=True)
        params[i][0][:] -= lr * dW
        params[i][1][:] -= lr * db

        if i > 0:  # propagate through ReLU of previous layer
            dA = dA @ params[i][0].T * relu_d(cache[i][0])

    return params

def train(X_tr, y_tr, X_te, y_te, layer_sizes, lr=0.01, epochs=120):
    params = init_weights(layer_sizes)
    # make params mutable lists of lists for in-place update
    params = [[W.copy(), b.copy()] for W, b in params]
    hist = {"train_loss": [], "test_loss": [], "train_acc": [], "test_acc": []}

    for _ in range(epochs):
        cache = forward(X_tr, params)
        params = backward_and_update(cache, params, y_tr, lr)

        pred_tr = forward(X_tr, params)[-1][1]
        pred_te = forward(X_te, params)[-1][1]
        hist["train_loss"].append(bce_loss(y_tr, pred_tr))
        hist["test_loss"].append(bce_loss(y_te, pred_te))
        hist["train_acc"].append(accuracy(y_tr, pred_tr))
        hist["test_acc"].append(accuracy(y_te, pred_te))

    return hist

# ── Models ─────────────────────────────────────────────────────────────────────
models = {
    "M1: 2→16→1":          [2, 16, 1],
    "M2: 2→16→16→1":       [2, 16, 16, 1],
    "M3: 2→16→16→16→1":    [2, 16, 16, 16, 1],
    "M4: 2→16×4→1":        [2, 16, 16, 16, 16, 1],
}

results = {}
for name, arch in models.items():
    print(f"Training {name} ...", end=" ", flush=True)
    results[name] = train(X_train, y_train, X_test, y_test, arch)
    print(f"done  |  test acc = {results[name]['test_acc'][-1]:.4f}")

epochs_range = np.arange(1, 121)
colors = ["steelblue", "tomato", "seagreen", "darkorange"]

# ── Plot: Loss curves ──────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for ax, (name, hist), c in zip(axes.flatten(), results.items(), colors):
    ax.plot(epochs_range, hist["train_loss"], label="Train Loss", color=c)
    ax.plot(epochs_range, hist["test_loss"],  label="Test Loss",  color=c, linestyle="--", alpha=0.7)
    ax.set_title(name)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss (BCE)")
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.suptitle("Training vs Testing Loss – Effect of Network Depth", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("plots/q2_loss_curves.png", dpi=150)
print("Saved: plots/q2_loss_curves.png")

# ── Plot: Accuracy curves ──────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for ax, (name, hist), c in zip(axes.flatten(), results.items(), colors):
    ax.plot(epochs_range, hist["train_acc"], label="Train Acc", color=c)
    ax.plot(epochs_range, hist["test_acc"],  label="Test Acc",  color=c, linestyle="--", alpha=0.7)
    ax.set_title(name)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Accuracy")
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.suptitle("Training vs Testing Accuracy – Effect of Network Depth", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("plots/q2_accuracy_curves.png", dpi=150)
print("Saved: plots/q2_accuracy_curves.png")
