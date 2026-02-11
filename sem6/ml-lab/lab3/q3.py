import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("Iris.csv")
df.drop(columns=["Id"], inplace=True)

df["Species"] = df["Species"].map({
    "Iris-setosa": 0,
    "Iris-versicolor": 1,
    "Iris-virginica": 2
})

X = df[["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]].values
y = df["Species"].values

def softmax(z):
    z = z - np.max(z, axis=1, keepdims=True)
    exp_z = np.exp(z)
    return exp_z / np.sum(exp_z, axis=1, keepdims=True)

def one_hot(y, c):
    return np.eye(c)[y]

def train_logistic_regression(X, y, lr=0.01, epochs=1000):
    n, d = X.shape
    c = len(np.unique(y))
    Xb = np.c_[np.ones(n), X]
    Y = one_hot(y, c)
    W = np.zeros((d + 1, c))

    for _ in range(epochs):
        probs = softmax(Xb @ W)
        grad = (1 / n) * Xb.T @ (probs - Y)
        W -= lr * grad

    return W

def predict(X, W):
    Xb = np.c_[np.ones(len(X)), X]
    probs = softmax(Xb @ W)
    preds = np.argmax(probs, axis=1)
    return preds, probs

def confusion_matrix(y_true, y_pred, c):
    cm = np.zeros((c, c), dtype=int)
    for t, p in zip(y_true, y_pred):
        cm[t, p] += 1
    return cm

def metrics_from_cm(cm):
    results = []
    for i in range(len(cm)):
        TP = cm[i, i]
        FP = cm[:, i].sum() - TP
        FN = cm[i, :].sum() - TP
        TN = cm.sum() - (TP + FP + FN)

        precision = TP / (TP + FP)
        recall = TP / (TP + FN)
        specificity = TN / (TN + FP)
        f1 = 2 * precision * recall / (precision + recall)

        results.append((precision, recall, specificity, f1))
    return results

def roc_auc(y_true, probs, cls):
    thresholds = np.linspace(0, 1, 100)
    TPR, FPR = [], []

    y_bin = (y_true == cls).astype(int)

    for t in thresholds:
        y_pred = (probs[:, cls] >= t).astype(int)
        TP = np.sum((y_pred == 1) & (y_bin == 1))
        FP = np.sum((y_pred == 1) & (y_bin == 0))
        FN = np.sum((y_pred == 0) & (y_bin == 1))
        TN = np.sum((y_pred == 0) & (y_bin == 0))

        TPR.append(TP / (TP + FN))
        FPR.append(FP / (FP + TN))

    auc = np.trapezoid(TPR, FPR)
    return np.array(FPR), np.array(TPR), auc

W = train_logistic_regression(X, y)
y_pred, probs = predict(X, W)

accuracy = np.mean(y == y_pred)
cm = confusion_matrix(y, y_pred, 3)
metrics = metrics_from_cm(cm)

print(f"Accuracy: {accuracy:.2f}")
print(f"\nConfusion Matrix:\n {cm}")

for i, (p, r, s, f1) in enumerate(metrics):
    print(f"\nClass {i:.2f}")
    print(f"Precision: {p:.2f}")
    print(f"Recall: {r:.2f}")
    print(f"Specificity: {s:.2f}")
    print(f"F1-score: {f1:.2f}")

print("\n")

for cls in range(3):
    fpr, tpr, auc = roc_auc(y, probs, cls)
    print(f"Class {cls} AUC:", auc)
    plt.plot(fpr, tpr, label=f"Class {cls} (AUC={auc:.2f})")

plt.plot([0, 1], [0, 1], linestyle="--")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve (One-vs-Rest)")
plt.legend()
plt.savefig("q3.png")
