import numpy as np
import time

# Logistic Regression (same as before)

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


def predict_lr(X, w, b):
    probs = sigmoid(np.dot(X, w) + b)
    return (probs >= 0.5).astype(int)


# Gaussian Naive Bayes

def train_gnb(X, y):

    classes = np.unique(y)
    mean = {}
    var = {}
    prior = {}

    for c in classes:
        X_c = X[y == c]

        mean[c] = np.mean(X_c, axis=0)
        var[c] = np.var(X_c, axis=0)
        prior[c] = X_c.shape[0] / X.shape[0]

    return mean, var, prior


def gaussian_prob(x, mean, var):
    eps = 1e-6
    coeff = 1 / np.sqrt(2 * np.pi * var + eps)
    exp = np.exp(-(x - mean)**2 / (2 * var + eps))
    return coeff * exp


def predict_gnb(X, mean, var, prior):

    preds = []

    for x in X:

        probs = {}

        for c in mean:

            likelihood = gaussian_prob(x, mean[c], var[c])
            probs[c] = np.log(prior[c]) + np.sum(np.log(likelihood))

        preds.append(max(probs, key=probs.get))

    return np.array(preds)


# Metrics

def accuracy(y_true, y_pred):
    return np.mean(y_true == y_pred)


def confusion_matrix(y_true, y_pred):

    tp = np.sum((y_true == 1) & (y_pred == 1))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))

    return np.array([[tn, fp],
                     [fn, tp]])


# Dataset generator

def generate_dataset(n_samples, random_features):

    X_informative = np.random.randn(n_samples, 2)

    y = (X_informative[:,0] + X_informative[:,1] > 0).astype(int)

    noise = np.random.randn(n_samples, random_features)

    X = np.hstack((X_informative, noise))

    return X, y


# Experiments

experiments = [0, 5, 20, 50]

for noise_features in experiments:

    print("\nExperiment with", noise_features, "random features")

    X, y = generate_dataset(500, noise_features)

    # Logistic Regression
    start = time.time()
    w, b = train_logistic_regression(X, y)
    lr_time = time.time() - start

    lr_preds = predict_lr(X, w, b)

    print("\nLogistic Regression")
    print("Accuracy:", accuracy(y, lr_preds))
    print("Training Time:", lr_time)
    print("Confusion Matrix:")
    print(confusion_matrix(y, lr_preds))

    # Gaussian Naive Bayes
    start = time.time()
    mean, var, prior = train_gnb(X, y)
    gnb_time = time.time() - start

    gnb_preds = predict_gnb(X, mean, var, prior)

    print("\nGaussian Naive Bayes")
    print("Accuracy:", accuracy(y, gnb_preds))
    print("Training Time:", gnb_time)
    print("Confusion Matrix:")
    print(confusion_matrix(y, gnb_preds))
