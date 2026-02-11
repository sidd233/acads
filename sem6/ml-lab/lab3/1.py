import numpy as np
import pandas as pd
import numpy as np
import pandas as pd

df = pd.read_csv("suv_data.csv")
df.drop(columns=["User ID"], inplace=True)
df["Gender"] = df["Gender"].map({"Male": 0, "Female": 1})

X = df[["Gender", "Age", "EstimatedSalary"]].values
y = df["Purchased"].values.reshape(-1, 1)

X = (X - X.mean(axis=0)) / X.std(axis=0)

np.random.seed(0)
indices = np.random.permutation(len(X))
split = int(0.75 * len(X))

train_idx, test_idx = indices[:split], indices[split:]
X_train, X_test = X[train_idx], X[test_idx]
y_train, y_test = y[train_idx], y[test_idx]

def sigmoid(z):
    return 1 / (1 + np.exp(-z))

def train(X, y, lr=0.1, epochs=2000):
    n_samples, n_features = X.shape
    Xb = np.c_[np.ones(n_samples), X]
    W = np.zeros((n_features + 1, 1))
    for _ in range(epochs):
        scores = Xb @ W
        probs = sigmoid(scores)
        gradient = (1 / n_samples) * Xb.T @ (probs - y)
        W -= lr * gradient
    return W

def predict(X, W):
    Xb = np.c_[np.ones(len(X)), X]
    probs = sigmoid(Xb @ W)
    return (probs >= 0.5).astype(int)

def accuracy(y_true, y_pred):
    return np.mean(y_true == y_pred)

W = train(X_train, y_train)
y_pred = predict(X_test, W)

acc = accuracy(y_test, y_pred)
print("Accuracy:", acc)

df = pd.read_csv("suv_data.csv")
df.drop(columns=["User ID"], inplace=True)
df["Gender"] = df["Gender"].map({"Male": 0, "Female": 1})

X = df[["Gender", "Age", "EstimatedSalary"]].values
y = df["Purchased"].values.reshape(-1, 1)

X = (X - X.mean(axis=0)) / X.std(axis=0)

np.random.seed(0)
indices = np.random.permutation(len(X))
split = int(0.7 * len(X))

train_idx, test_idx = indices[:split], indices[split:]
X_train, X_test = X[train_idx], X[test_idx]
y_train, y_test = y[train_idx], y[test_idx]

def sigmoid(z):
    return 1 / (1 + np.exp(-z))

def train(X, y, lr=0.1, epochs=2000):
    n_samples, n_features = X.shape
    Xb = np.c_[np.ones(n_samples), X]
    W = np.zeros((n_features + 1, 1))
    for _ in range(epochs):
        scores = Xb @ W
        probs = sigmoid(scores)
        gradient = (1 / n_samples) * Xb.T @ (probs - y)
        W -= lr * gradient
    return W

def predict(X, W):
    Xb = np.c_[np.ones(len(X)), X]
    probs = sigmoid(Xb @ W)
    return (probs >= 0.5).astype(int)

def accuracy(y_true, y_pred):
    return np.mean(y_true == y_pred)

W = train(X_train, y_train)
y_pred = predict(X_test, W)

acc = accuracy(y_test, y_pred)
print("Accuracy:", acc)
