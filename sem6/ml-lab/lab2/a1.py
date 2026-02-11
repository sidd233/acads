import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

np.random.seed(0)

data = np.random.randint(1,100,(500,4))
df = pd.DataFrame(data,columns=["ID","TV","Radio","Newspaper"])
df["Sales"] = 3*df["TV"] + 4*df["Radio"] + 5*df["Newspaper"] + np.random.randint(0,1000,500)

df = df.sample(frac=1).reset_index(drop=True)

X = df[["TV","Radio","Newspaper"]].values
Y = df["Sales"].values.reshape(-1,1)

split = int(0.7*len(X))
X_train,X_test = X[:split],X[split:]
Y_train,Y_test = Y[:split],Y[split:]

X_train = (X_train - X_train.mean(axis=0)) / X_train.std(axis=0)
X_test = (X_test - X_test.mean(axis=0)) / X_test.std(axis=0)

X_train = np.c_[np.ones((X_train.shape[0],1)),X_train]
X_test = np.c_[np.ones((X_test.shape[0],1)),X_test]

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

Y_pred = X_test @ theta

plt.scatter(Y_test,Y_pred)
plt.xlabel("Actual Sales")
plt.ylabel("Predicted Sales")
plt.savefig("q1.png")