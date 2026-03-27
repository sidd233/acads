import numpy as np
import matplotlib.pyplot as plt
import os

os.makedirs("plots", exist_ok=True)

rng = np.random.default_rng(42)
N = 1000
x1 = rng.uniform(-3, 3, N)
x2 = rng.uniform(-3, 3, N)
z = x1**2 + x2**2 - 4
y_clean = (z > 0).astype(int)
X = np.column_stack([x1, x2])


def gini(y):
    if len(y) == 0:
        return 0.0
    p = np.mean(y)
    return 1 - p**2 - (1 - p)**2


def best_split(X, y, min_samples=5):
    best_g = float('inf')
    best_f = None
    best_t = None
    for f in range(X.shape[1]):
        vals = np.unique(X[:, f])
        thresholds = (vals[:-1] + vals[1:]) / 2
        for t in thresholds:
            mask = X[:, f] <= t
            if mask.sum() < min_samples or (~mask).sum() < min_samples:
                continue
            g = (mask.sum() * gini(y[mask]) + (~mask).sum() * gini(y[~mask])) / len(y)
            if g < best_g:
                best_g = g
                best_f = f
                best_t = t
    return best_f, best_t


def build(X, y, depth, max_depth, min_samples=5):
    if depth >= max_depth or len(y) < min_samples or len(np.unique(y)) == 1:
        return int(np.round(np.mean(y)))
    f, t = best_split(X, y, min_samples)
    if f is None:
        return int(np.round(np.mean(y)))
    mask = X[:, f] <= t
    return (f, t, build(X[mask], y[mask], depth+1, max_depth, min_samples),
                   build(X[~mask], y[~mask], depth+1, max_depth, min_samples))


def predict(tree, X):
    def pred_one(node, x):
        if not isinstance(node, tuple):
            return node
        f, t, l, r = node
        return pred_one(l, x) if x[f] <= t else pred_one(r, x)
    return np.array([pred_one(tree, x) for x in X])


def accuracy(y_true, y_pred):
    return np.mean(y_true == y_pred)


def add_label_noise(y, rate, rng):
    y_noisy = y.copy()
    flip = rng.random(len(y)) < rate
    y_noisy[flip] = 1 - y_noisy[flip]
    return y_noisy


def add_feature_noise(X, std, rng):
    return X + rng.normal(0, std, X.shape)


MAX_DEPTH = 6

label_noise_rates = [0.0, 0.1, 0.2, 0.3]
label_accs = []

for rate in label_noise_rates:
    y_noisy = add_label_noise(y_clean, rate, rng)
    tree = build(X, y_noisy, 0, MAX_DEPTH)
    preds = predict(tree, X)
    acc = accuracy(y_clean, preds)
    label_accs.append(acc)
    print(f"Label noise {int(rate*100):>3}% | Train acc (vs clean labels): {acc:.4f}")

feature_noise_stds = [0.0, 0.2, 0.5, 1.0]
feature_accs = []

for std in feature_noise_stds:
    X_noisy = add_feature_noise(X, std, rng)
    tree = build(X_noisy, y_clean, 0, MAX_DEPTH)
    preds = predict(tree, X)
    acc = accuracy(y_clean, preds)
    feature_accs.append(acc)
    print(f"Feature noise std={std:.1f}  | Test acc (clean features): {acc:.4f}")

fig, axes = plt.subplots(1, 2, figsize=(10, 4))

axes[0].plot([int(r*100) for r in label_noise_rates], label_accs, marker='o')
axes[0].set_xlabel("Label Noise (%)")
axes[0].set_ylabel("Accuracy (vs clean labels)")
axes[0].set_title("Effect of Label Noise")
axes[0].set_ylim(0, 1)

axes[1].plot(feature_noise_stds, feature_accs, marker='o', color='orange')
axes[1].set_xlabel("Feature Noise Std")
axes[1].set_ylabel("Accuracy (on clean features)")
axes[1].set_title("Effect of Feature Noise")
axes[1].set_ylim(0, 1)

plt.tight_layout()
plt.savefig("plots/q4_noise_comparison.png", dpi=100)
plt.close()

xx, yy = np.meshgrid(np.linspace(-3, 3, 200), np.linspace(-3, 3, 200))
grid = np.c_[xx.ravel(), yy.ravel()]

fig, axes = plt.subplots(1, 4, figsize=(16, 4))
for ax, rate in zip(axes, label_noise_rates):
    y_noisy = add_label_noise(y_clean, rate, rng)
    tree = build(X, y_noisy, 0, MAX_DEPTH)
    Z = predict(tree, grid).reshape(xx.shape)
    ax.contourf(xx, yy, Z, alpha=0.3, cmap='RdBu')
    ax.scatter(x1, x2, c=y_noisy, cmap='RdBu', s=3, edgecolors='none')
    ax.set_title(f"Label noise {int(rate*100)}%")
    ax.set_xlabel("x1")
    ax.set_ylabel("x2")

plt.tight_layout()
plt.savefig("plots/q4_label_noise_boundaries.png", dpi=100)
plt.close()

fig, axes = plt.subplots(1, 4, figsize=(16, 4))
for ax, std in zip(axes, feature_noise_stds):
    X_noisy = add_feature_noise(X, std, rng)
    tree = build(X_noisy, y_clean, 0, MAX_DEPTH)
    Z = predict(tree, grid).reshape(xx.shape)
    ax.contourf(xx, yy, Z, alpha=0.3, cmap='RdBu')
    ax.scatter(x1, x2, c=y_clean, cmap='RdBu', s=3, edgecolors='none')
    ax.set_title(f"Feature noise std={std:.1f}")
    ax.set_xlabel("x1")
    ax.set_ylabel("x2")

plt.tight_layout()
plt.savefig("plots/q4_feature_noise_boundaries.png", dpi=100)
plt.close()
