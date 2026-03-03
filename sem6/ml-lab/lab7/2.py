# ==============================================================================
# L1 vs L2 Regularisation in Logistic Regression
# ==============================================================================

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Create output directory for plots
os.makedirs("plots", exist_ok=True)

np.random.seed(42)

print("\n" + "=" * 60)
print("Logistic Regression : L1 vs L2 Regularisation")
print("=" * 60)

# ── Dataset Generation ──────────────────────────────────────────────────────
N2 = 600
X2 = np.random.uniform(-1, 1, (N2, 5))
eps2 = np.random.normal(0, 0.2, N2)
z = 2*X2[:,0] - 3*X2[:,1] + 0.5*X2[:,2]**2 - X2[:,3]*X2[:,4] + eps2
y2 = (z > 0).astype(int)

split2 = int(0.7 * N2)
idx2 = np.random.permutation(N2)
X2_tr, X2_te = X2[idx2[:split2]], X2[idx2[split2:]]
y2_tr, y2_te = y2[idx2[:split2]], y2[idx2[split2:]]

# Normalise
mu2 = X2_tr.mean(axis=0);  sig2 = X2_tr.std(axis=0) + 1e-8
X2_tr_n = (X2_tr - mu2) / sig2
X2_te_n = (X2_te - mu2) / sig2

def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -500, 500)))

def logistic_predict(X, w, b):
    return sigmoid(X @ w + b)

def accuracy(y_true, y_pred_prob):
    return np.mean((y_pred_prob >= 0.5).astype(int) == y_true)

def train_logistic(X_tr, y_tr, X_te, y_te, epochs=100, lr=0.1,
                   reg_type=None, lam=0.0):
    n_feat = X_tr.shape[1]
    w = np.zeros(n_feat)
    b = 0.0
    train_acc_hist = []
    test_acc_hist  = []

    for _ in range(epochs):
        p = logistic_predict(X_tr, w, b)
        err = p - y_tr
        grad_w = (X_tr.T @ err) / len(y_tr)
        grad_b = err.mean()

        if reg_type == "l2":
            grad_w += lam * w
        elif reg_type == "l1":
            grad_w += lam * np.sign(w)

        w -= lr * grad_w
        b -= lr * grad_b

        if reg_type == "l1":
            # Soft-thresholding
            w = np.sign(w) * np.maximum(np.abs(w) - lr * lam, 0)

        train_acc_hist.append(accuracy(y_tr, logistic_predict(X_tr, w, b)))
        test_acc_hist.append(accuracy(y_te, logistic_predict(X_te, w, b)))

    return w, b, train_acc_hist, test_acc_hist

# ── Part A: No Regularisation ────────────────────────────────────────────────
w_none, b_none, tr_acc, te_acc = train_logistic(
    X2_tr_n, y2_tr, X2_te_n, y2_te, reg_type=None, lam=0)
EPOCHS = 100
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(range(1, EPOCHS+1), tr_acc, label="Train Accuracy", color="steelblue")
ax.plot(range(1, EPOCHS+1), te_acc, label="Test Accuracy",  color="tomato", linestyle="--")
ax.set_title("Part A : Logistic Regression (No Regularisation)")
ax.set_xlabel("Epoch");  ax.set_ylabel("Accuracy")
ax.legend();  ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("plots/q2a_no_reg_accuracy.png", dpi=150)
plt.close()
print(f"  No Reg | Final Train Acc: {tr_acc[-1]:.4f} | Test Acc: {te_acc[-1]:.4f}")

# ── Part B: L2 Regularisation ────────────────────────────────────────────────
lambdas = np.round(np.arange(0, 1.1, 0.1), 2)
l2_test_accs = []
for lam in lambdas:
    _, _, _, te_a = train_logistic(X2_tr_n, y2_tr, X2_te_n, y2_te, reg_type="l2", lam=lam)
    l2_test_accs.append(te_a[-1])
    print(f"  L2 λ={lam:.1f} | Final Test Acc: {te_a[-1]:.4f}")

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(lambdas, l2_test_accs, "o-", color="steelblue")
ax.set_title("Q2 Part B – L2 Regularisation: Test Accuracy vs λ")
ax.set_xlabel("λ");  ax.set_ylabel("Final Test Accuracy")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("plots/q2b_l2_test_accuracy.png", dpi=150)
plt.close()

# ── Part C: L1 Regularisation ────────────────────────────────────────────────
l1_test_accs   = []
l1_nonzero     = []
for lam in lambdas:
    w_l1, _, _, te_a = train_logistic(X2_tr_n, y2_tr, X2_te_n, y2_te, reg_type="l1", lam=lam)
    l1_test_accs.append(te_a[-1])
    l1_nonzero.append(np.sum(np.abs(w_l1) > 1e-4))
    print(f"  L1 λ={lam:.1f} | Final Test Acc: {te_a[-1]:.4f} | Non-zero coefs: {l1_nonzero[-1]}")

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(lambdas, l1_test_accs, "o-", color="tomato")
axes[0].set_title("Q2 Part C – L1: Test Accuracy vs λ")
axes[0].set_xlabel("λ");  axes[0].set_ylabel("Final Test Accuracy")
axes[0].grid(True, alpha=0.3)

axes[1].plot(lambdas, l1_nonzero, "s-", color="darkorange")
axes[1].set_title("Q2 Part C – L1: Non-zero Coefficients vs λ")
axes[1].set_xlabel("λ");  axes[1].set_ylabel("# Non-zero Coefficients")
axes[1].set_yticks(range(0, 6))
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("plots/q2c_l1_accuracy_and_sparsity.png", dpi=150)
plt.close()
print("\n  Saved all plots in 'plots/' directory.")