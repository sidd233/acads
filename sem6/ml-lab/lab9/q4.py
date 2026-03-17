import numpy as np
import matplotlib.pyplot as plt

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


# ── XOR Dataset ───────────────────────────────────────────────────────────────
X = np.array([[0, 0],
              [0, 1],
              [1, 0],
              [1, 1]], dtype=float)
y = np.array([[0], [1], [1], [0]], dtype=float)

# ── MLP: 2 → 6 → 1  (bias in every neuron, ReLU hidden, Sigmoid output) ─────
np.random.seed(0)
W1 = np.random.randn(2, 6) * 0.5
b1 = np.zeros((1, 6))
W2 = np.random.randn(6, 1) * 0.5
b2 = np.zeros((1, 1))

lr     = 0.1
epochs = 100

train_losses = []

for _ in range(epochs):
    # Forward
    Z1 = X @ W1 + b1
    A1 = relu(Z1)
    Z2 = A1 @ W2 + b2
    A2 = sigmoid(Z2)

    train_losses.append(bce_loss(A2, y))

    # Backward
    n   = X.shape[0]
    dZ2 = (A2 - y) / n
    dW2 = A1.T @ dZ2
    db2 = dZ2.sum(axis=0, keepdims=True)

    dZ1 = (dZ2 @ W2.T) * relu_deriv(Z1)
    dW1 = X.T @ dZ1
    db1 = dZ1.sum(axis=0, keepdims=True)

    W2 -= lr * dW2;  b2 -= lr * db2
    W1 -= lr * dW1;  b1 -= lr * db1

# Final predictions
A2_final = sigmoid(relu(X @ W1 + b1) @ W2 + b2)
print("XOR Predictions after training:")
for xi, yi, pi in zip(X, y, A2_final):
    print(f"  Input: {xi.astype(int)}  True: {int(yi[0])}  "
          f"Pred: {pi[0]:.4f}  Class: {int(pi[0] >= 0.5)}")

# ── Plot convergence ──────────────────────────────────────────────────────────
plt.figure(figsize=(7, 5))
plt.plot(train_losses, color="darkorange", lw=2, label="Training Loss")
plt.xlabel("Epoch")
plt.ylabel("BCE Loss")
plt.title("Q4: XOR Classification – Training Loss Convergence  (2 → 6 → 1)")
plt.legend()
plt.tight_layout()
plt.savefig("q4_results.png", dpi=120)
plt.show()
print("Saved → q4_results.png")
