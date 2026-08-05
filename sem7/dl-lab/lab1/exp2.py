"""
Deep Learning Lab Assignment 1 - Experiment II
Learning Behaviour of a Single Layer Perceptron
================================================

Covers:
  1. 2D linearly separable dataset, 40 samples (20/20)
  2. 2D scatter plot of the dataset
  3. Perceptron init with random weights/bias + standard PLA
  4. Animated decision boundary, updated after every weight update
  5. Live display of w, b, iteration, boundary, #misclassified,
     the sample responsible for the update, and angle between
     consecutive weight vectors
  6. Stops when converged or max_iter reached
  7. Misclassified-count vs iteration plot
  8. Sweep over learning rate, weight init, bias init, feature scaling

Run:  python3 perceptron_experiment2.py
Outputs are written to ./outputs/
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless rendering, safe for saving files
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)
np.random.seed(7)


# ---------------------------------------------------------------------------
# 1 & 2. Dataset generation + static scatter plot
# ---------------------------------------------------------------------------
def generate_dataset(n_per_class=20, mean0=(-1.2, -1.2), mean1=(1.2, 1.2),
                      spread=1.0, seed=None):
    """40 samples total, 20 per class, linearly separable by construction
    (two well-separated Gaussian blobs)."""
    rng = np.random.default_rng(seed)
    cov = [[spread, 0], [0, spread]]
    X0 = rng.multivariate_normal(mean0, cov, n_per_class)
    X1 = rng.multivariate_normal(mean1, cov, n_per_class)
    X = np.vstack([X0, X1])
    y = np.array([0] * n_per_class + [1] * n_per_class)
    # shuffle so class order isn't trivially sorted
    perm = rng.permutation(len(y))
    return X[perm], y[perm]


def plot_dataset(X, y, path):
    plt.figure(figsize=(6, 6))
    plt.scatter(X[y == 0, 0], X[y == 0, 1], c="tab:red", marker="o", label="Class 0", edgecolor="k")
    plt.scatter(X[y == 1, 0], X[y == 1, 1], c="tab:blue", marker="^", label="Class 1", edgecolor="k")
    plt.axhline(0, color="gray", lw=0.5)
    plt.axvline(0, color="gray", lw=0.5)
    plt.xlabel("x1")
    plt.ylabel("x2")
    plt.title("Generated 2D Linearly Separable Dataset (40 samples)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()


# ---------------------------------------------------------------------------
# 3 & 5 & 6. Perceptron Learning Algorithm (PLA), matching the pseudocode:
#   labels are {0,1} in the data, but PLA below uses the {-1,+1} convention
#   internally (equivalent update rule to the assignment's P/N formulation).
# ---------------------------------------------------------------------------
def train_perceptron(X, y, lr=1.0, w_init=None, b_init=None,
                      max_iter=500, seed=None):
    """
    Standard single-sample (stochastic) perceptron update:
        pick a currently-misclassified sample x with label y_signed
        w <- w + lr * y_signed * x
        b <- b + lr * y_signed

    Returns a list of history dicts, one entry per iteration *before* the
    update made at that iteration, so history[k] describes the state that
    produced the k-th update (or the final converged state if n_mis == 0).
    """
    rng = np.random.default_rng(seed)
    n_samples, n_features = X.shape

    w = (rng.uniform(-1, 1, n_features) if w_init is None else np.array(w_init, dtype=float))
    b = (rng.uniform(-1, 1) if b_init is None else float(b_init))

    y_signed = np.where(y == 1, 1, -1)

    history = []
    prev_w = w.copy()

    for it in range(max_iter):
        preds = X @ w + b
        misclassified = np.where(y_signed * preds <= 0)[0]
        n_mis = len(misclassified)

        if n_mis == 0:
            history.append(dict(iter=it, w=w.copy(), b=b, n_mis=0,
                                 updated_idx=None, angle=None))
            break

        idx = rng.choice(misclassified)

        cos_angle = np.dot(prev_w, w) / (np.linalg.norm(prev_w) * np.linalg.norm(w) + 1e-12)
        angle = np.degrees(np.arccos(np.clip(cos_angle, -1, 1))) if it > 0 else 0.0

        history.append(dict(iter=it, w=w.copy(), b=b, n_mis=n_mis,
                             updated_idx=idx, angle=angle))

        prev_w = w.copy()
        w = w + lr * y_signed[idx] * X[idx]
        b = b + lr * y_signed[idx]
    else:
        # max_iter reached without convergence: log the final state too
        preds = X @ w + b
        n_mis = int(np.sum(y_signed * preds <= 0))
        history.append(dict(iter=max_iter, w=w.copy(), b=b, n_mis=n_mis,
                             updated_idx=None, angle=None))

    return history


def boundary_xy(w, b, xlim):
    """Return two points describing the decision line w0*x + w1*y + b = 0."""
    x_vals = np.array(xlim)
    if abs(w[1]) > 1e-8:
        y_vals = -(w[0] * x_vals + b) / w[1]
    else:
        # vertical line fallback
        x_const = -b / (w[0] + 1e-12)
        x_vals = np.array([x_const, x_const])
        y_vals = np.array(xlim)
    return x_vals, y_vals


# ---------------------------------------------------------------------------
# 4 & 5. Animation of the learning process
# ---------------------------------------------------------------------------
def animate_training(X, y, history, path, title="Perceptron Learning"):
    y_signed = np.where(y == 1, 1, -1)
    xlim = (X[:, 0].min() - 1.5, X[:, 0].max() + 1.5)
    ylim = (X[:, 1].min() - 1.5, X[:, 1].max() + 1.5)

    fig, ax = plt.subplots(figsize=(7, 7))

    def draw(frame_idx):
        ax.clear()
        state = history[frame_idx]
        w, b, n_mis = state["w"], state["b"], state["n_mis"]

        preds = X @ w + b
        correct = y_signed * preds > 0

        ax.scatter(X[correct & (y == 0)][:, 0], X[correct & (y == 0)][:, 1],
                   c="tab:red", marker="o", edgecolor="k", label="Class 0 (correct)")
        ax.scatter(X[correct & (y == 1)][:, 0], X[correct & (y == 1)][:, 1],
                   c="tab:blue", marker="^", edgecolor="k", label="Class 1 (correct)")
        ax.scatter(X[~correct][:, 0], X[~correct][:, 1],
                   facecolor="none", edgecolor="orange", s=160, linewidth=2,
                   label="Misclassified")

        if state["updated_idx"] is not None:
            xi = X[state["updated_idx"]]
            ax.scatter(*xi, s=260, facecolor="none", edgecolor="lime", linewidth=2.5,
                       label="Sample used for update")

        bx, by = boundary_xy(w, b, xlim)
        ax.plot(bx, by, "k--", lw=2, label="Decision boundary")

        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_xlabel("x1")
        ax.set_ylabel("x2")

        angle_txt = f"{state['angle']:.2f}°" if state["angle"] is not None else "N/A"
        info = (f"Iteration: {state['iter']}\n"
                f"w = [{w[0]:.3f}, {w[1]:.3f}], b = {b:.3f}\n"
                f"Misclassified: {n_mis}/{len(X)}\n"
                f"Angle(w_prev, w_curr): {angle_txt}")
        ax.set_title(f"{title}\n{info}", fontsize=10, loc="left")
        ax.legend(loc="upper right", fontsize=7)

    anim = FuncAnimation(fig, draw, frames=len(history), interval=600, repeat=False)
    anim.save(path, writer=PillowWriter(fps=2))
    plt.close(fig)


# ---------------------------------------------------------------------------
# 7. Misclassified count vs iteration
# ---------------------------------------------------------------------------
def plot_convergence(history, path, label=None, ax=None, title="Misclassified samples vs Iteration"):
    iters = [h["iter"] for h in history]
    n_mis = [h["n_mis"] for h in history]
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(iters, n_mis, marker="o", markersize=3, label=label)
    ax.set_xlabel("Iteration")
    ax.set_ylabel("# Misclassified samples")
    ax.set_title(title)
    if label:
        ax.legend(fontsize=8)
    if standalone:
        plt.tight_layout()
        plt.savefig(path, dpi=130)
        plt.close(fig)
    return ax


# ---------------------------------------------------------------------------
# 8. Sweep: learning rate / weight init / bias init / feature scaling
# ---------------------------------------------------------------------------
def standardize(X):
    return (X - X.mean(axis=0)) / X.std(axis=0)


def run_sweep(X, y):
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # (a) Learning rate sweep
    ax = axes[0, 0]
    for lr in [0.01, 0.1, 1.0, 5.0]:
        h = train_perceptron(X, y, lr=lr, w_init=[0.1, 0.1], b_init=0.0, seed=1)
        plot_convergence(h, None, label=f"lr={lr}", ax=ax, title="(a) Effect of Learning Rate")

    # (b) Weight initialization sweep
    ax = axes[0, 1]
    for w0, tag in [([0.01, 0.01], "small (~0.01)"),
                    ([1.0, 1.0], "large (~1.0)"),
                    ([-2.0, 3.0], "large mismatched signs")]:
        h = train_perceptron(X, y, lr=1.0, w_init=w0, b_init=0.0, seed=1)
        plot_convergence(h, None, label=f"w_init={tag}", ax=ax, title="(b) Effect of Weight Init")

    # (c) Bias initialization sweep
    ax = axes[1, 0]
    for b0 in [0.0, 5.0, -5.0]:
        h = train_perceptron(X, y, lr=1.0, w_init=[0.1, 0.1], b_init=b0, seed=1)
        plot_convergence(h, None, label=f"b_init={b0}", ax=ax, title="(c) Effect of Bias Init")

    # (d) Feature scaling
    ax = axes[1, 1]
    X_scaled = standardize(X)
    h_raw = train_perceptron(X, y, lr=1.0, w_init=[0.1, 0.1], b_init=0.0, seed=1)
    h_scaled = train_perceptron(X_scaled, y, lr=1.0, w_init=[0.1, 0.1], b_init=0.0, seed=1)
    plot_convergence(h_raw, None, label="raw features", ax=ax, title="(d) Effect of Feature Scaling")
    plot_convergence(h_scaled, None, label="standardized features", ax=ax, title="(d) Effect of Feature Scaling")

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "sweep_comparison.png"), dpi=130)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # 1 & 2: dataset + scatter
    X, y = generate_dataset(n_per_class=20, seed=5)
    plot_dataset(X, y, os.path.join(OUT_DIR, "dataset_scatter.png"))

    # 3-6: train with random init and animate
    # (weights/bias initialised deliberately far from a good separator so the
    #  learning process is visible over several iterations)
    history = train_perceptron(X, y, lr=1.0, w_init=[-2.0, 3.0], b_init=4.0,
                                max_iter=200, seed=42)
    animate_training(X, y, history, os.path.join(OUT_DIR, "perceptron_learning.gif"))

    # 7: convergence plot for this run
    plot_convergence(history, os.path.join(OUT_DIR, "convergence_baseline.png"),
                      label="baseline (lr=1.0, random init)")

    # 8: sweep experiments
    run_sweep(X, y)

    print(f"Converged in {history[-1]['iter']} iterations "
          f"with final n_mis={history[-1]['n_mis']}")
    print("All outputs written to:", os.path.abspath(OUT_DIR))
