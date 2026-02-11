import numpy as np
import pandas as pd

df = pd.read_csv("Iris.csv")
df.drop(columns=["Id"], inplace=True)
df["Species"] = df["Species"].map({"Iris-setosa": 0, "Iris-versicolor": 1, "Iris-virginica": 2})

X = df[["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]].values
y = df["Species"].values

def softmax(z):
    exp_z = np.exp(z - np.max(z, axis=1, keepdims=True))
    return exp_z / np.sum(exp_z, axis=1, keepdims=True)

def one_hot(y, num_classes):
    return np.eye(num_classes)[y]

def accuracy(y_true, y_pred):
    return np.mean(y_true == y_pred)

def train(X, y, lr=0.01, epochs=1000):
    n_samples, n_features = X.shape
    n_classes = len(np.unique(y))

    X = np.c_[np.ones(n_samples), X]
    Y = one_hot(y, n_classes)

    W = np.zeros((n_features + 1, n_classes))

    for _ in range(epochs):
        scores = X @ W
        probs = softmax(scores)

        gradient = (1 / n_samples) * X.T @ (probs - Y)
        W -= lr * gradient

    return W

def skfcv_helper(y, k=5):
    classes = np.unique(y)
    class_indices = {c: np.where(y == c)[0] for c in classes}

    for c in classes:
        np.random.shuffle(class_indices[c])

    folds = [[] for _ in range(k)]

    for c in classes:
        splits = np.array_split(class_indices[c], k)
        for i in range(k):
            folds[i].extend(splits[i])

    return [np.array(fold) for fold in folds]


def skfcv(X, y, k=5):
    folds = skfcv_helper(y, k)
    accuracies = []

    for i in range(k):
        test_idx = folds[i]
        train_idx = np.hstack([folds[j] for j in range(k) if j != i])

        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        W = train(X_train, y_train)

        X_test_bias = np.c_[np.ones(len(X_test)), X_test]
        preds = np.argmax(softmax(X_test_bias @ W), axis=1)

        acc = accuracy(y_test, preds)
        accuracies.append(acc)

    return accuracies


accuracies = skfcv(X, y, 8)

print("Accuracy per fold:", accuracies)
print(f"Mean Accuracy: {np.mean(accuracies):.2f}")
