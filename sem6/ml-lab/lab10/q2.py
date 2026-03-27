import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.tree import DecisionTreeClassifier

os.makedirs("plots", exist_ok=True)

rng = np.random.default_rng(0)
N = 500
X = rng.standard_normal((N, 2))
y = ((X[:, 0] ** 2 + X[:, 1] ** 2) < 1.5).astype(int)


class DecisionTreeScratch:
    def __init__(self, max_depth=5, min_samples=2):
        self.max_depth = max_depth
        self.min_samples = min_samples
        self.tree = None

    def _gini(self, y):
        if len(y) == 0:
            return 0.0
        p = np.mean(y)
        return 1 - p**2 - (1 - p)**2

    def _best_split(self, X, y):
        best_gini = float('inf')
        best_feat = None
        best_thresh = None
        for feat in range(X.shape[1]):
            vals = np.unique(X[:, feat])
            thresholds = (vals[:-1] + vals[1:]) / 2
            for t in thresholds:
                left = y[X[:, feat] <= t]
                right = y[X[:, feat] > t]
                if len(left) < self.min_samples or len(right) < self.min_samples:
                    continue
                g = (len(left) * self._gini(left) + len(right) * self._gini(right)) / len(y)
                if g < best_gini:
                    best_gini = g
                    best_feat = feat
                    best_thresh = t
        return best_feat, best_thresh

    def _build(self, X, y, depth):
        if depth >= self.max_depth or len(y) < self.min_samples or len(np.unique(y)) == 1:
            return int(np.round(np.mean(y)))
        feat, thresh = self._best_split(X, y)
        if feat is None:
            return int(np.round(np.mean(y)))
        mask = X[:, feat] <= thresh
        left = self._build(X[mask], y[mask], depth + 1)
        right = self._build(X[~mask], y[~mask], depth + 1)
        return (feat, thresh, left, right)

    def fit(self, X, y):
        self.tree = self._build(X, y, 0)

    def _predict_one(self, node, x):
        if not isinstance(node, tuple):
            return node
        feat, thresh, left, right = node
        if x[feat] <= thresh:
            return self._predict_one(left, x)
        return self._predict_one(right, x)

    def predict(self, X):
        return np.array([self._predict_one(self.tree, x) for x in X])


def numpy_accuracy(y_true, y_pred):
    return np.mean(y_true == y_pred)


def plot_boundary_2d(X, y, model, title, path):
    xx, yy = np.meshgrid(np.linspace(X[:, 0].min() - 0.5, X[:, 0].max() + 0.5, 200),
                         np.linspace(X[:, 1].min() - 0.5, X[:, 1].max() + 0.5, 200))
    grid = np.c_[xx.ravel(), yy.ravel()]
    Z = model.predict(grid).reshape(xx.shape)
    fig, ax = plt.subplots()
    ax.contourf(xx, yy, Z, alpha=0.3, cmap='RdBu')
    ax.scatter(X[:, 0], X[:, 1], c=y, cmap='RdBu', s=10, edgecolors='none')
    ax.set_title(title)
    ax.set_xlabel("x1")
    ax.set_ylabel("x2")
    plt.tight_layout()
    plt.savefig(path, dpi=100)
    plt.close()


depths = [3, 5, 7]
scratch_accs = []
sklearn_accs = []

for d in depths:
    model = DecisionTreeScratch(max_depth=d)
    model.fit(X, y)
    preds = model.predict(X)
    acc = numpy_accuracy(y, preds)
    scratch_accs.append(acc)
    print(f"[Scratch] Depth {d} | Accuracy: {acc:.4f}")
    plot_boundary_2d(X, y, model, f"Scratch DT (depth={d})", f"plots/q2_scratch_depth{d}.png")

for d in depths:
    clf = DecisionTreeClassifier(max_depth=d, criterion='gini', random_state=0)
    clf.fit(X, y)
    preds = clf.predict(X)
    acc = numpy_accuracy(y, preds)
    sklearn_accs.append(acc)
    print(f"[sklearn] Depth {d} | Accuracy: {acc:.4f}")
    plot_boundary_2d(X, y, clf, f"sklearn DT (depth={d})", f"plots/q2_sklearn_depth{d}.png")

print("\nAccuracy Comparison:")
print(f"{'Depth':<8} {'Scratch':>10} {'sklearn':>10}")
for d, sa, ka in zip(depths, scratch_accs, sklearn_accs):
    print(f"{d:<8} {sa:>10.4f} {ka:>10.4f}")
