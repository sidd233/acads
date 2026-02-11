import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# fish dataset not available so using a real estate dataset from kaggle

df = pd.read_csv("Real_Estate.csv")

X = df[["House age",
        "Distance to the nearest MRT station",
        "Number of convenience stores",
        "Latitude",
        "Longitude"]].values

Y = df["House price of unit area"].values.reshape(-1,1)

np.random.seed(42)
idx = np.random.permutation(len(X))
X = X[idx]
Y = Y[idx]

split = int(0.7 * len(X))
X_train, X_test = X[:split], X[split:]
Y_train, Y_test = Y[:split], Y[split:]

mu = X_train.mean(axis=0)
sigma = X_train.std(axis=0)
X_train = (X_train - mu) / sigma
X_test = (X_test - mu) / sigma

X_train = np.c_[np.ones((X_train.shape[0],1)), X_train]
X_test = np.c_[np.ones((X_test.shape[0],1)), X_test]

print("Training set inputs :",X_train)
print("Training set outputs :",Y_train)
print("Testing set inputs :",X_test)
print("Testing set outputs :",Y_test)

theta = np.zeros((X_train.shape[1],1))
lr = 0.01
epochs = 2000
m = len(X_train)

for i in range(epochs):
    y_pred = X_train @ theta
    error = y_pred - Y_train
    grad = (1/m) * X_train.T @ error
    theta = theta - lr * grad

Y_pred_test = X_test @ theta

plt.scatter(Y_test, Y_pred_test)
plt.xlabel("Actual Price")
plt.ylabel("Predicted Price")
plt.savefig("q3.png")
plt.close()
