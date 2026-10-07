"""
Task 4 helpers: analytical least-squares reference, convergence detection,
loss-surface evaluation, and regression metrics.
"""

import numpy as np


def least_squares_solution(X, y):
    """Closed-form least-squares solution w* = (X^T X)^-1 X^T y."""
    return np.linalg.inv(X.T @ X) @ (X.T @ y)


def loss_surface(X, y, w1_range, w2_range):
    """Full-training-set MSE evaluated over a (w1, w2) grid."""
    W1, W2 = np.meshgrid(w1_range, w2_range)
    W = np.stack([W1.ravel(), W2.ravel()], axis=0)   # (2, n_grid)
    preds = X @ W                                     # (n_samples, n_grid)
    Z = np.mean((y[:, None] - preds) ** 2, axis=0).reshape(W1.shape)
    return W1, W2, Z


def loss_along_path(X, y, weight_history):
    """Full-training-set MSE at every stored weight snapshot."""
    preds = X @ weight_history.T                      # (n_samples, n_points)
    return np.mean((y[:, None] - preds) ** 2, axis=0)  # (n_points,)


def find_convergence_epoch(epoch_loss, j_star, tol=1.01, patience=5):
    """1-based epoch at which full-training-set MSE first stays
    <= tol * j_star for `patience` consecutive epochs. None if it never does."""
    threshold = tol * j_star
    streak = 0
    for i, loss in enumerate(epoch_loss):
        if loss <= threshold:
            streak += 1
            if streak == patience:
                return i - patience + 2  # 1-based index of streak start
        else:
            streak = 0
    return None


def subsample_path(weight_history, max_points=1500):
    """Thin a trajectory for plotting while always keeping first/last points."""
    n = weight_history.shape[0]
    if n <= max_points:
        return weight_history
    idx = np.linspace(0, n - 1, max_points).round().astype(int)
    idx[-1] = n - 1
    return weight_history[idx]


def regression_metrics(y_true, y_pred):
    mse = np.mean((y_true - y_pred) ** 2)
    rmse = np.sqrt(mse)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1 - ss_res / ss_tot
    return mse, rmse, r2


def trajectory_behaviour(weight_history):
    """Ratio of actual path length to straight-line start->end distance, as a
    rough smoothness proxy, mapped to a qualitative label."""
    diffs = np.diff(weight_history, axis=0)
    path_length = np.sum(np.linalg.norm(diffs, axis=1))
    straight = np.linalg.norm(weight_history[-1] - weight_history[0])
    ratio = path_length / straight if straight > 1e-12 else np.inf

    if ratio < 1.5:
        label = "smooth, direct descent"
    elif ratio < 4:
        label = "mildly noisy path"
    else:
        label = "noisy / oscillatory path"
    return ratio, label
