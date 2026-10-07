"""
Single-neuron linear regression model: y_hat = w1*x1 + w2*x2 (no bias).
Shared by Task 2 (demo training) and Task 3 (nine optimizers).
"""

import numpy as np


class SingleNeuron:
    def __init__(self, w1_init=1.5, w2_init=-1.5):
        self.w = np.array([w1_init, w2_init], dtype=float)

    def forward(self, X):
        """Linear activation: y_hat = X @ w = w1*x1 + w2*x2."""
        return X @ self.w

    @staticmethod
    def mse_loss(y_true, y_pred):
        return np.mean((y_true - y_pred) ** 2)

    @staticmethod
    def gradients(X, y_true, y_pred):
        """dMSE/dw for w = [w1, w2], MSE = mean((y_true - y_pred)^2)."""
        n = X.shape[0]
        error = y_pred - y_true
        return (2.0 / n) * (X.T @ error)
