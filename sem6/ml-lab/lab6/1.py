import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

np.random.seed(42)

# ---------- utilities ----------
def r2_score(y, yhat):
    ss_res = np.sum((y - yhat)**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    return 1 - ss_res/ss_tot

def poly_features(X, degree):
    feats = [np.ones((X.shape[0], 1))]
    for d in range(1, degree+1):
        feats.append(X**d)
    return np.hstack(feats)

# ---------- data ----------
n = 600
X = np.random.uniform(-1, 1, (n, 5))
eps = np.random.normal(0, 0.2, n)
y = 3*X[:,0]**2 + 2*X[:,1]*X[:,2] + 0.5*X[:,3]**3 - X[:,4] + eps
split = int(0.7*n)
x_train, x_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

# ---------- Part A ----------
final_train, final_test = [], []

for d in range(1, 7):
    x_train_p = poly_features(x_train, d)
    x_test_p = poly_features(x_test, d)
    w = np.zeros(x_train_p.shape[1])
    tr_curve, te_curve = [], []

    for _ in range(100):
        yhat = x_train_p @ w
        grad = -2 * x_train_p.T @ (y_train - yhat) / len(y_train)
        w -= 0.01 * grad

        tr_curve.append(r2_score(y_train, x_train_p @ w))
        te_curve.append(r2_score(y_test, x_test_p @ w))

    final_train.append(tr_curve[-1])
    final_test.append(te_curve[-1])

    plt.figure()
    plt.plot(tr_curve, label="train")
    plt.plot(te_curve, label="test")
    plt.xlabel("epoch")
    plt.ylabel("R2")
    plt.title(f"Degree {d}")
    plt.legend()
    plt.savefig(f"1_x{d}.png")

plt.figure()
plt.plot(range(1,7), final_train, label="train")
plt.plot(range(1,7), final_test, label="test")
plt.xlabel("degree")
plt.ylabel("final R2")
plt.legend()
plt.savefig("1_1.png")

# ---------- Part B ----------
d = 6
x_train_p = poly_features(x_train, d)
x_test_p = poly_features(x_test, d)

lambdas = np.arange(0, 1.1, 0.1)
tr_l2, te_l2 = [], []

for l in lambdas:
    w = np.zeros(x_train_p.shape[1])
    for _ in range(100):
        yhat = x_train_p @ w
        grad = -2 * x_train_p.T @ (y_train - yhat) / len(y_train) + 2*l*w
        w -= 0.01 * grad
    tr_l2.append(r2_score(y_train, x_train_p @ w))
    te_l2.append(r2_score(y_test, x_test_p @ w))

plt.figure()
plt.plot(lambdas, tr_l2, label="train")
plt.plot(lambdas, te_l2, label="test")
plt.xlabel("lambda")
plt.ylabel("final R2")
plt.legend()
plt.savefig("1_2.png")
