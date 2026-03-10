import numpy as np
import matplotlib.pyplot as plt

# Helper functions

def sigmoid(z):
    return 1/(1+np.exp(-z))


def loss(y, p):
    eps = 1e-9
    return -np.mean(y*np.log(p+eps) + (1-y)*np.log(1-p+eps))


def accuracy(y, y_pred):
    return np.mean(y == y_pred)


# Dataset generation

def generate_linear_dataset(n=500):

    x1 = np.random.uniform(-2,2,n)
    x2 = np.random.uniform(-2,2,n)

    eps = np.random.normal(0,0.2,n)

    z = 2*x1 + 3*x2 + eps
    y = (z > 0).astype(int)

    X = np.column_stack((x1,x2))
    return X,y


def generate_nonlinear_dataset(n=500):

    x1 = np.random.uniform(-2,2,n)
    x2 = np.random.uniform(-2,2,n)

    eps = np.random.normal(0,0.2,n)

    z = x1**2 + x2**2 - 1 + eps
    y = (z > 0).astype(int)

    X = np.column_stack((x1,x2))
    return X,y


# Train/test split

def split_data(X,y):

    idx = np.random.permutation(len(X))
    split = int(0.7*len(X))

    train = idx[:split]
    test = idx[split:]

    return X[train],X[test],y[train],y[test]

# Logistic Regression Training

def train_lr(X_train,y_train,X_test,y_test,epochs=200,lr=0.1):

    n_samples,n_features = X_train.shape

    w = np.zeros(n_features)
    b = 0

    train_acc=[]
    test_acc=[]
    losses=[]

    for _ in range(epochs):

        z = np.dot(X_train,w)+b
        p = sigmoid(z)

        dw = (1/n_samples)*np.dot(X_train.T,(p-y_train))
        db = (1/n_samples)*np.sum(p-y_train)

        w -= lr*dw
        b -= lr*db

        preds_train = (p>=0.5).astype(int)
        preds_test = (sigmoid(np.dot(X_test,w)+b)>=0.5).astype(int)

        train_acc.append(accuracy(y_train,preds_train))
        test_acc.append(accuracy(y_test,preds_test))
        losses.append(loss(y_train,p))

    return w,b,train_acc,test_acc,losses


# Plot functions

def plot_accuracy(train_acc,test_acc,name):

    plt.figure()

    plt.plot(train_acc,label="Train Accuracy")
    plt.plot(test_acc,label="Test Accuracy")

    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.title(name+" Accuracy vs Epoch")

    plt.legend()

    plt.savefig("3_"+name+"_accuracy.png")
    plt.close()


def plot_loss(losses,name):

    plt.figure()

    plt.plot(losses)

    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title(name+" Loss vs Epoch")

    plt.savefig("3_"+name+"_loss.png")
    plt.close()


def plot_boundary(X,y,w,b,name):

    plt.figure()

    plt.scatter(X[:,0],X[:,1],c=y,cmap="coolwarm")

    x_vals = np.linspace(X[:,0].min(),X[:,0].max(),100)
    y_vals = -(w[0]*x_vals+b)/w[1]

    plt.plot(x_vals,y_vals)

    plt.title(name+" Decision Boundary")

    plt.savefig("3_"+name+"_boundary.png")
    plt.close()


# Run Experiment

datasets = [
    ("Dataset_A", generate_linear_dataset()),
    ("Dataset_B", generate_nonlinear_dataset())
]

for name,(X,y) in datasets:

    X_train,X_test,y_train,y_test = split_data(X,y)

    w,b,train_acc,test_acc,losses = train_lr(
        X_train,y_train,X_test,y_test
    )

    plot_accuracy(train_acc,test_acc,name)
    plot_loss(losses,name)
    plot_boundary(X,y,w,b,name)