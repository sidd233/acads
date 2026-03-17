import numpy as np
import matplotlib.pyplot as plt

np.random.seed(42)

# ── Activation functions ──────────────────────────────────────────────────────

def relu(x):
    return np.maximum(0, x)

def relu_deriv(x):
    return (x > 0).astype(float)

def sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

def bce_loss(y_pred, y_true):
    eps = 1e-9
    return -np.mean(
        y_true * np.log(y_pred + eps) + (1 - y_true) * np.log(1 - y_pred + eps)
    )

def accuracy(y_pred, y_true):
    return np.mean((y_pred >= 0.5) == y_true)


# ── Dataset ───────────────────────────────────────────────────────────────────
N = 600
x1 = np.random.uniform(-3, 3, N)
x2 = np.random.uniform(-3, 3, N)
eps = np.random.normal(0, 0.5, N)
z   = x1**2 + x2**2 - 4 + eps
y   = (z > 0).astype(float).reshape(-1, 1)
X   = np.column_stack([x1, x2])          # (600, 2)

# Train / test split 70 / 30
n_train = int(0.7 * N)
idx     = np.random.permutation(N)
X_train, X_test = X[idx[:n_train]], X[idx[n_train:]]
y_train, y_test = y[idx[:n_train]], y[idx[n_train:]]

# ── MLP: 2 → 16 → 1  (ReLU hidden, Sigmoid output) ──────────────────────────
np.random.seed(42)
W1 = np.random.randn(2, 16) * 0.1
b1 = np.zeros((1, 16))
W2 = np.random.randn(16, 1) * 0.1
b2 = np.zeros((1, 1))

lr     = 0.01
epochs = 200

train_losses, test_losses = [], []
train_accs,   test_accs   = [], []

for _ in range(epochs):
    # Forward – train
    Z1 = X_train @ W1 + b1
    A1 = relu(Z1)
    A2 = sigmoid(A1 @ W2 + b2)

    # Forward – test
    A2t = sigmoid(relu(X_test @ W1 + b1) @ W2 + b2)

    train_losses.append(bce_loss(A2,  y_train))
    test_losses .append(bce_loss(A2t, y_test))
    train_accs  .append(accuracy(A2,  y_train))
    test_accs   .append(accuracy(A2t, y_test))

    # Backward
    n   = X_train.shape[0]
    dZ2 = (A2 - y_train) / n
    dW2 = A1.T @ dZ2
    db2 = dZ2.sum(axis=0, keepdims=True)

    dZ1 = (dZ2 @ W2.T) * relu_deriv(Z1)
    dW1 = X_train.T @ dZ1
    db1 = dZ1.sum(axis=0, keepdims=True)

    W2 -= lr * dW2;  b2 -= lr * db2
    W1 -= lr * dW1;  b1 -= lr * db1

print(f"Final Train Acc : {train_accs[-1]:.4f}")
print(f"Final Test  Acc : {test_accs [-1]:.4f}")

# ── Plots ─────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Q3: Decision Boundary Learning  (2 → 16 → 1)")

# Loss curves
ax = axes[0]
ax.plot(train_losses, label="Train Loss")
ax.plot(test_losses,  label="Test Loss")
ax.set_xlabel("Epoch");  ax.set_ylabel("BCE Loss")
ax.set_title("Training & Testing Loss")
ax.legend()

# Decision boundary
ax  = axes[1]
res = 300
xx, yy = np.meshgrid(np.linspace(-3, 3, res), np.linspace(-3, 3, res))
grid   = np.column_stack([xx.ravel(), yy.ravel()])
Ag     = sigmoid(relu(grid @ W1 + b1) @ W2 + b2).reshape(xx.shape)

ax.contourf(xx, yy, Ag, levels=[0, 0.5, 1], alpha=0.25, colors=["steelblue", "salmon"])
ax.contour (xx, yy, Ag, levels=[0.5], colors="black", linewidths=1.5)

theta = np.linspace(0, 2 * np.pi, 200)
ax.plot(2 * np.cos(theta), 2 * np.sin(theta), "g--", lw=1.5, label="True boundary (r=2)")

c0 = y_test[:, 0] == 0
ax.scatter(X_test[ c0, 0], X_test[ c0, 1], c="steelblue", s=12, alpha=0.6, label="Class 0")
ax.scatter(X_test[~c0, 0], X_test[~c0, 1], c="salmon",    s=12, alpha=0.6, label="Class 1")
ax.set_xlabel("x1");  ax.set_ylabel("x2")
ax.set_title("Learned vs True Decision Boundary")
ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig("q3_results.png", dpi=120)