import numpy as np
import matplotlib.pyplot as plt

np.random.seed(42)

def accuracy(y, yhat):
    return np.mean(y == yhat)

def sigmoid(z):
    return 1/(1+np.exp(-z))

# ---------- data ----------
n = 500
X = np.random.uniform(-1, 1, (n, 5))
eps = np.random.normal(0, 0.1, n)
z = X[:,0]**2 + X[:,1]**2 + 0.5*X[:,2] - X[:,3]*X[:,4] + eps
y = (z > 0.5).astype(int)

split = int(0.7*n)
x_train, x_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

x_train = np.c_[np.ones(len(x_train)), x_train]
x_test = np.c_[np.ones(len(x_test)), x_test]

# ---------- Part A ----------
w = np.zeros(x_train.shape[1])
tr_acc, te_acc = [], []

for _ in range(100):
    p = sigmoid(x_train @ w)
    grad = x_train.T @ (p - y_train) / len(y_train)
    w -= 0.1 * grad

    tr_acc.append(accuracy(y_train, (sigmoid(x_train @ w) > 0.5)))
    te_acc.append(accuracy(y_test, (sigmoid(x_test @ w) > 0.5)))

plt.figure()
plt.plot(tr_acc, label="train")
plt.plot(te_acc, label="test")
plt.xlabel("epoch")
plt.ylabel("accuracy")
plt.legend()
plt.savefig("2_1.png")

# ---------- Part B ----------
lambdas = np.arange(0, 1.1, 0.1)
accs = []

for l in lambdas:
    w = np.zeros(x_train.shape[1])
    for _ in range(100):
        p = sigmoid(x_train @ w)
        grad = x_train.T @ (p - y_train) / len(y_train) + l*w
        w -= 0.1 * grad
    accs.append(accuracy(y_test, (sigmoid(x_test @ w) > 0.5)))

plt.figure()
plt.plot(lambdas, accs)
plt.xlabel("lambda")
plt.ylabel("final accuracy")
plt.savefig("2_2.png")
