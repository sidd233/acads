import os
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(42)
os.makedirs("plots", exist_ok=True)

# ---------------------------------
# Dataset Generation
# ---------------------------------
n_samples = 700

X = np.random.uniform(-2, 2, n_samples)
epsilon = np.random.normal(0, np.sqrt(0.5), n_samples)   # Increased noise
y = np.sin(np.pi * X) + 0.3 * (X**2) + epsilon

# Shuffle
indices = np.random.permutation(n_samples)
X = X[indices]
y = y[indices]

# Small training set to force overfitting
train_size = 80
X_train = X[:train_size]
y_train = y[:train_size]
X_test = X[train_size:]
y_test = y[train_size:]

# ---------------------------------
# Helper Functions
# ---------------------------------

def polynomial_features(x, degree):
    return np.vstack([x**d for d in range(degree + 1)]).T

def mse(y_true, y_pred):
    return np.mean((y_true - y_pred) ** 2)

def train_model_closed_form(X_train, y_train, X_test, y_test, degree):
    Xtr = polynomial_features(X_train, degree)
    Xte = polynomial_features(X_test, degree)

    # Standardize
    mean = Xtr.mean(axis=0)
    std = Xtr.std(axis=0)
    std[std == 0] = 1

    Xtr = (Xtr - mean) / std
    Xte = (Xte - mean) / std

    # Normal equation using pseudo-inverse
    w = np.linalg.pinv(Xtr.T @ Xtr) @ Xtr.T @ y_train

    train_mse = mse(y_train, Xtr @ w)
    test_mse = mse(y_test, Xte @ w)

    return train_mse, test_mse

# ---------------------------------
# Experiment
# ---------------------------------

degrees = [1, 3, 5, 7, 9, 11, 15, 20, 25]

final_train = []
final_test = []

for d in degrees:
    train_mse, test_mse = train_model_closed_form(
        X_train, y_train, X_test, y_test, d
    )

    final_train.append(train_mse)
    final_test.append(test_mse)

# ---------------------------------
# Final Bias–Variance Plot
# ---------------------------------

plt.figure()
plt.plot(degrees, final_train)
plt.plot(degrees, final_test)
plt.xlabel("Polynomial Degree")
plt.ylabel("Final MSE")
plt.legend(["Training MSE", "Testing MSE"])
plt.title("Bias–Variance Tradeoff")
plt.savefig("plots/q1_mse_vs_degree.png")
plt.close()
print("\n  Saved all plots in 'plots/' directory.")