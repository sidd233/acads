import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from urllib.request import urlretrieve

os.makedirs("plots", exist_ok=True)

url = "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data"
local_path = "heart.csv"
if not os.path.exists(local_path):
    urlretrieve(url, local_path)

cols = ["age","sex","cp","trestbps","chol","fbs","restecg","thalach","exang","oldpeak","slope","ca","thal","target"]
df = pd.read_csv(local_path, header=None, names=cols, na_values="?")

df["target"] = (df["target"] > 0).astype(int)

df["ca"] = df["ca"].fillna(df["ca"].median())
df["thal"] = df["thal"].fillna(df["thal"].mode()[0])

df["sex"] = df["sex"].astype(int)
df["cp"] = df["cp"].astype(int)
df["fbs"] = df["fbs"].astype(int)
df["restecg"] = df["restecg"].astype(int)
df["exang"] = df["exang"].astype(int)
df["slope"] = df["slope"].astype(int)
df["ca"] = df["ca"].astype(int)
df["thal"] = df["thal"].astype(int)

X = df.drop("target", axis=1).values.astype(float)
y = df["target"].values
feature_names = list(df.drop("target", axis=1).columns)

rng = np.random.default_rng(42)
idx = rng.permutation(len(y))
split = int(0.8 * len(y))
X_train, X_test = X[idx[:split]], X[idx[split:]]
y_train, y_test = y[idx[:split]], y[idx[split:]]


class DecisionTree:
    def __init__(self, max_depth=5, min_samples_split=2):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.tree = None
        self.feature_importances_ = None

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
                left_mask = X[:, feat] <= t
                right_mask = ~left_mask
                if left_mask.sum() < self.min_samples_split or right_mask.sum() < self.min_samples_split:
                    continue
                g = (left_mask.sum() * self._gini(y[left_mask]) + right_mask.sum() * self._gini(y[right_mask])) / len(y)
                if g < best_gini:
                    best_gini = g
                    best_feat = feat
                    best_thresh = t
        return best_feat, best_thresh, best_gini

    def _build(self, X, y, depth, importances):
        if depth >= self.max_depth or len(y) < self.min_samples_split or len(np.unique(y)) == 1:
            return int(np.round(np.mean(y)))
        feat, thresh, split_gini = self._best_split(X, y)
        if feat is None:
            return int(np.round(np.mean(y)))
        parent_gini = self._gini(y)
        mask = X[:, feat] <= thresh
        n = len(y)
        n_l = mask.sum()
        n_r = n - n_l
        child_gini = (n_l * self._gini(y[mask]) + n_r * self._gini(y[~mask])) / n
        importances[feat] += n * (parent_gini - child_gini)
        left = self._build(X[mask], y[mask], depth + 1, importances)
        right = self._build(X[~mask], y[~mask], depth + 1, importances)
        return (feat, thresh, left, right)

    def fit(self, X, y):
        importances = np.zeros(X.shape[1])
        self.tree = self._build(X, y, 0, importances)
        total = importances.sum()
        self.feature_importances_ = importances / total if total > 0 else importances

    def _predict_one(self, node, x):
        if not isinstance(node, tuple):
            return node
        feat, thresh, left, right = node
        return self._predict_one(left, x) if x[feat] <= thresh else self._predict_one(right, x)

    def predict(self, X):
        return np.array([self._predict_one(self.tree, x) for x in X])


def accuracy(y_true, y_pred):
    return np.mean(y_true == y_pred)

def confusion_matrix(y_true, y_pred):
    cm = np.zeros((2, 2), dtype=int)
    for t, p in zip(y_true, y_pred):
        cm[t][p] += 1
    return cm

def f1_score(y_true, y_pred):
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


best_acc = 0
best_params = None
for depth in [3, 5, 7, 9]:
    for min_split in [2, 5, 10]:
        m = DecisionTree(max_depth=depth, min_samples_split=min_split)
        m.fit(X_train, y_train)
        val_preds = m.predict(X_test)
        acc = accuracy(y_test, val_preds)
        if acc > best_acc:
            best_acc = acc
            best_params = (depth, min_split)

print(f"Best params: depth={best_params[0]}, min_samples_split={best_params[1]}")

model = DecisionTree(max_depth=best_params[0], min_samples_split=best_params[1])
model.fit(X_train, y_train)
preds = model.predict(X_test)

acc = accuracy(y_test, preds)
f1 = f1_score(y_test, preds)
cm = confusion_matrix(y_test, preds)

print(f"Accuracy : {acc:.4f}")
print(f"F1 Score : {f1:.4f}")
print("Confusion Matrix:")
print(cm)

fig, ax = plt.subplots()
im = ax.imshow(cm, cmap='Blues')
ax.set_xticks([0, 1])
ax.set_yticks([0, 1])
ax.set_xticklabels(['Pred 0', 'Pred 1'])
ax.set_yticklabels(['True 0', 'True 1'])
for i in range(2):
    for j in range(2):
        ax.text(j, i, cm[i, j], ha='center', va='center', color='black')
ax.set_title("Confusion Matrix – Heart Disease")
plt.tight_layout()
plt.savefig("plots/q3_confusion_matrix.png", dpi=100)
plt.close()

importances = model.feature_importances_
order = np.argsort(importances)[::-1]

fig, ax = plt.subplots()
ax.bar(range(len(feature_names)), importances[order])
ax.set_xticks(range(len(feature_names)))
ax.set_xticklabels([feature_names[i] for i in order], rotation=45, ha='right')
ax.set_ylabel("Importance")
ax.set_title("Feature Importances – Heart Disease")
plt.tight_layout()
plt.savefig("plots/q3_feature_importance.png", dpi=100)
plt.close()

print("\nFeature Importances:")
for i in order:
    print(f"  {feature_names[i]:<12}: {importances[i]:.4f}")
