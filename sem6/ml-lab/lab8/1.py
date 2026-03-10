import numpy as np
import matplotlib.pyplot as plt

# Helper functions

def sigmoid(z):
    return 1 / (1 + np.exp(-z))


def train_logistic_regression(X, y, lr=0.1, epochs=1000):

    n_samples, n_features = X.shape
    weights = np.zeros(n_features)
    bias = 0

    for _ in range(epochs):

        linear = np.dot(X, weights) + bias
        preds = sigmoid(linear)

        dw = (1/n_samples) * np.dot(X.T, (preds - y))
        db = (1/n_samples) * np.sum(preds - y)

        weights -= lr * dw
        bias -= lr * db

    return weights, bias


def predict(X, weights, bias):
    linear = np.dot(X, weights) + bias
    probs = sigmoid(linear)
    return (probs >= 0.5).astype(int)


def accuracy(y_true, y_pred):
    return np.mean(y_true == y_pred)


def confusion_matrix(y_true, y_pred):

    tp = np.sum((y_true == 1) & (y_pred == 1))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))

    return np.array([[tn, fp], [fn, tp]])


def plot_decision_boundary(X, y, w, b, title, filename):

    plt.figure()

    plt.scatter(X[:,0], X[:,1], c=y, cmap='bwr')

    x_vals = np.linspace(X[:,0].min(), X[:,0].max(), 100)
    y_vals = -(w[0]*x_vals + b) / w[1]

    plt.plot(x_vals, y_vals)

    plt.title(title)

    plt.savefig(filename)
    plt.close()

# Dataset A (Linearly Separable)

np.random.seed(0)

class0 = np.random.randn(200,2) + np.array([-2,-2])
class1 = np.random.randn(200,2) + np.array([2,2])

X_A = np.vstack((class0, class1))
y_A = np.array([0]*200 + [1]*200)


# Dataset B (Overlapping)

class0 = np.random.randn(200,2) + np.array([-1,-1])
class1 = np.random.randn(200,2) + np.array([1,1])

X_B = np.vstack((class0, class1))
y_B = np.array([0]*200 + [1]*200)

# Dataset C (Circular Boundary)

n = 400
theta = 2*np.pi*np.random.rand(n)
r = np.sqrt(np.random.rand(n))

x1 = r * np.cos(theta)
x2 = r * np.sin(theta)

X_C = np.column_stack((x1,x2))

radius = np.sqrt(x1**2 + x2**2)
y_C = (radius > 0.5).astype(int)


datasets = [
    ("Dataset A (Linear)", X_A, y_A),
    ("Dataset B (Overlap)", X_B, y_B),
    ("Dataset C (Circular)", X_C, y_C)
]

# Run the experiment

for name, X, y in datasets:

    weights, bias = train_logistic_regression(X, y)

    preds = predict(X, weights, bias)

    acc = accuracy(y, preds)
    cm = confusion_matrix(y, preds)

    print("\n", name)
    print("Accuracy:", acc)
    print("Confusion Matrix:")
    print(cm)

    filename = "1_" + name.replace(" ", "_") + ".png"

    plot_decision_boundary(X, y, weights, bias, name, filename)