import numpy as np
import matplotlib.pyplot as plt

# Logistic Regression (from scratch)
def sigmoid(z):
    return 1 / (1 + np.exp(-z))

def train_logistic_regression(X, y, lr=0.1, epochs=5000):
    n, d = X.shape
    w = np.zeros(d)
    b = 0.0

    for _ in range(epochs):
        z = X @ w + b
        y_hat = sigmoid(z)

        dw = (1 / n) * (X.T @ (y_hat - y))
        db = (1 / n) * np.sum(y_hat - y)

        w -= lr * dw
        b -= lr * db

    return w, b

def predict(X, w, b):
    return (sigmoid(X @ w + b) >= 0.5).astype(int)

# convex hull (using monotone chain algorithm)
def convex_hull(points):
    points = np.unique(points, axis=0)
    points = points[np.lexsort((points[:,1], points[:,0]))]

    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])

    lower = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(tuple(p))

    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(tuple(p))

    hull = lower[:-1] + upper[:-1]
    return np.array(hull)

def plot_hull(hull, color):
    hull = np.vstack([hull, hull[0]])
    plt.plot(hull[:,0], hull[:,1], color)

# decision boundary
def plot_decision_boundary(X, w, b):
    x_min, x_max = X[:,0].min()-1, X[:,0].max()+1
    y_min, y_max = X[:,1].min()-1, X[:,1].max()+1
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, 300),
                         np.linspace(y_min, y_max, 300))
    Z = sigmoid(xx*w[0] + yy*w[1] + b)
    plt.contour(xx, yy, Z, levels=[0.5], linewidths=2)

# case 1: linearly separable
N = 50
X1 = np.random.randn(N, 2) + np.array([-4, 0])
X2 = np.random.randn(N, 2) + np.array([4, 0])

X = np.vstack((X1, X2))
y = np.hstack((np.zeros(N), np.ones(N)))

w, b = train_logistic_regression(X, y)
y_pred = predict(X, w, b)
print("Linearly separable accuracy:", np.mean(y_pred == y))

plt.figure()
plt.scatter(X1[:,0], X1[:,1], label="Class C1")
plt.scatter(X2[:,0], X2[:,1], label="Class C2")
plot_decision_boundary(X, w, b)
plot_hull(convex_hull(X1), 'b')
plot_hull(convex_hull(X2), 'r')
plt.title("Linearly Separable Dataset")
plt.legend()
plt.savefig("q2_1.png")

# case 2: non-linearly separable
X1 = np.random.randn(N, 2) + np.array([0, 0])
X2 = np.random.randn(N, 2) + np.array([1, 1])

X = np.vstack((X1, X2))
y = np.hstack((np.zeros(N), np.ones(N)))

w, b = train_logistic_regression(X, y)
y_pred = predict(X, w, b)
print("Non-linearly separable accuracy:", np.mean(y_pred == y))

plt.figure()
plt.scatter(X1[:,0], X1[:,1], label="Class C1")
plt.scatter(X2[:,0], X2[:,1], label="Class C2")
plot_decision_boundary(X, w, b)
plot_hull(convex_hull(X1), 'b')
plot_hull(convex_hull(X2), 'r')
plt.title("Non-linearly Separable Dataset")
plt.legend()
plt.savefig("q2_2.png")
