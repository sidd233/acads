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

def kfcv(X, y, k=5):
    indices = np.random.permutation(len(X))
    folds = np.array_split(indices, k)

    accuracies = []

    for i in range(k):
        test_idx = folds[i]
        train_idx = np.hstack(folds[:i] + folds[i+1:])

        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        W = train(X_train, y_train)

        X_test_bias = np.c_[np.ones(len(X_test)), X_test]
        preds = np.argmax(softmax(X_test_bias @ W), axis=1)

        acc = accuracy(y_test, preds)
        accuracies.append(acc)

    return accuracies

accuracies = kfcv(X, y, k=5)

print("Accuracy per fold:", accuracies)
print(f"Mean Accuracy: {np.mean(accuracies):.2f}")
