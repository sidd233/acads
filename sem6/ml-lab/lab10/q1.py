import numpy as np
import matplotlib.pyplot as plt
import os

rng = np.random.default_rng(42)
N = 800
x1 = rng.uniform(-2, 2, N)
x2 = rng.uniform(-2, 2, N)
z = x1 + x2 + 0.3 * np.sin(3 * x1)
y = (z > 0).astype(int)

os.makedirs("plots", exist_ok=True)

def gini(labels):
    if len(labels) == 0:
        return 0.0
    p = np.mean(labels)
    return 1 - p**2 - (1 - p)**2

def best_split(X, y):
    best_gini = float('inf')
    best_feat = None
    best_thresh = None
    n_features = X.shape[1]
    for feat in range(n_features):
        thresholds = np.unique(X[:, feat])
        for t in thresholds:
            left = y[X[:, feat] <= t]
            right = y[X[:, feat] > t]
            if len(left) == 0 or len(right) == 0:
                continue
            g = (len(left) * gini(left) + len(right) * gini(right)) / len(y)
            if g < best_gini:
                best_gini = g
                best_feat = feat
                best_thresh = t
    return best_feat, best_thresh

def build_tree(X, y, depth, max_depth):
    if depth == max_depth or len(np.unique(y)) == 1:
        return np.round(np.mean(y)).astype(int)
    feat, thresh = best_split(X, y)
    if feat is None:
        return np.round(np.mean(y)).astype(int)
    left_mask = X[:, feat] <= thresh
    right_mask = ~left_mask
    left = build_tree(X[left_mask], y[left_mask], depth + 1, max_depth)
    right = build_tree(X[right_mask], y[right_mask], depth + 1, max_depth)
    return (feat, thresh, left, right)

def predict_one(tree, x):
    if not isinstance(tree, tuple):
        return tree
    feat, thresh, left, right = tree
    if x[feat] <= thresh:
        return predict_one(left, x)
    else:
        return predict_one(right, x)

def predict(tree, X):
    return np.array([predict_one(tree, x) for x in X])

def plot_boundary(X, y, tree, title, path):
    xx, yy = np.meshgrid(
        np.linspace(-2, 2, 300),
        np.linspace(-2, 2, 300)
    )
    grid = np.c_[xx.ravel(), yy.ravel()]
    Z = predict(tree, grid).reshape(xx.shape)
    fig, ax = plt.subplots()
    ax.contourf(xx, yy, Z, alpha=0.3, cmap='RdBu')
    ax.scatter(X[:, 0], X[:, 1], c=y, cmap='RdBu', s=5, edgecolors='none')
    ax.set_title(title)
    ax.set_xlabel("x1")
    ax.set_ylabel("x2")
    plt.tight_layout()
    plt.savefig(path, dpi=100)
    plt.close()

X2d = np.column_stack([x1, x2])
depths = [2, 4, 6, 8, 10]

for d in depths:
    tree = build_tree(X2d, y, 0, d)
    preds = predict(tree, X2d)
    acc = np.mean(preds == y)
    print(f"Depth {d} | Accuracy: {acc:.4f}")
    plot_boundary(X2d, y, tree, f"Decision Boundary (depth={d})", f"plots/q1_depth{d}.png")

X3d = np.column_stack([x1, x2, x1 + x2])

for d in depths:
    tree = build_tree(X3d, y, 0, d)
    preds = predict(tree, X3d)
    acc = np.mean(preds == y)
    print(f"[x3] Depth {d} | Accuracy: {acc:.4f}")
    xx, yy = np.meshgrid(np.linspace(-2, 2, 300), np.linspace(-2, 2, 300))
    grid = np.c_[xx.ravel(), yy.ravel(), xx.ravel() + yy.ravel()]
    Z = predict(tree, grid).reshape(xx.shape)
    fig, ax = plt.subplots()
    ax.contourf(xx, yy, Z, alpha=0.3, cmap='RdBu')
    ax.scatter(x1, x2, c=y, cmap='RdBu', s=5, edgecolors='none')
    ax.set_title(f"Decision Boundary x3 (depth={d})")
    ax.set_xlabel("x1")
    ax.set_ylabel("x2")
    plt.tight_layout()
    plt.savefig(f"plots/q1_x3_depth{d}.png", dpi=100)
    plt.close()
