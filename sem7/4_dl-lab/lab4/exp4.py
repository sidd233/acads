import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers 3D projection)

from exp1 import prepare_data
from optimizers import run_all_optimizers, MAX_EPOCHS
from analysis import (
    least_squares_solution, loss_surface, loss_along_path,
    find_convergence_epoch, subsample_path, regression_metrics,
    trajectory_behaviour,
)

OPTIMIZER_NAMES = [
    "BGD", "MBGD", "Momentum GD", "SGD", "SGD with Momentum",
    "NAG", "Nesterov SGD", "AdaGrad", "RMSProp",
]


def inverse_transform(y_std, y_scaler):
    return y_scaler.mean_[0] + y_std * y_scaler.std_[0]


def build_optimizer_stats(results, X_train, y_train, X_test, y_test, y_scaler, j_star):
    """Per-optimizer derived quantities used by every plot/table in this file."""
    stats = {}
    for name in OPTIMIZER_NAMES:
        r = results[name]
        wh = r["weight_history"]

        path_loss = loss_along_path(X_train, y_train, wh)
        lowest_idx = int(np.argmin(path_loss))

        conv_epoch = find_convergence_epoch(r["epoch_loss"], j_star)

        w_final = r["w_final"]
        y_train_pred_std = X_train @ w_final
        y_test_pred_std = X_test @ w_final

        y_train_orig = inverse_transform(y_train, y_scaler)
        y_test_orig = inverse_transform(y_test, y_scaler)
        y_train_pred_orig = inverse_transform(y_train_pred_std, y_scaler)
        y_test_pred_orig = inverse_transform(y_test_pred_std, y_scaler)

        train_mse, _, _ = regression_metrics(y_train_orig, y_train_pred_orig)
        test_mse, test_rmse, test_r2 = regression_metrics(y_test_orig, y_test_pred_orig)

        ratio, behaviour_label = trajectory_behaviour(wh)

        stats[name] = dict(
            weight_history=wh,
            epoch_loss=r["epoch_loss"],
            n_updates=r["n_updates"],
            w_final=w_final,
            path_loss=path_loss,
            lowest_idx=lowest_idx,
            lowest_w=wh[lowest_idx],
            lowest_loss=path_loss[lowest_idx],
            conv_epoch=conv_epoch,
            train_mse=train_mse,
            test_mse=test_mse,
            test_rmse=test_rmse,
            test_r2=test_r2,
            y_test_orig=y_test_orig,
            y_test_pred_orig=y_test_pred_orig,
            smoothness_ratio=ratio,
            behaviour_label=behaviour_label,
        )
    return stats

def plot_contour_grid(stats, W1, W2, Z, w_star, save_path="task4_contours.png"):
    fig, axes = plt.subplots(3, 3, figsize=(14, 13))
    fig.suptitle("Task 4: Optimizer Trajectories on MSE Contour (w1, w2)")

    for ax, name in zip(axes.ravel(), OPTIMIZER_NAMES):
        s = stats[name]
        ax.contour(W1, W2, Z, levels=25, cmap="Greys", linewidths=0.6)

        path = subsample_path(s["weight_history"], max_points=1500)
        ax.plot(path[:, 0], path[:, 1], color="tab:orange", lw=1, alpha=0.85, zorder=3)

        ax.scatter(*s["weight_history"][0], color="green", s=40, zorder=5, label="start")
        ax.scatter(*s["weight_history"][-1], color="red", s=40, zorder=5, label="final")
        ax.scatter(*s["lowest_w"], color="purple", marker="*", s=90, zorder=6, label="lowest loss")
        ax.scatter(*w_star, color="black", marker="x", s=60, zorder=6, label="J* (analytical)")

        ax.set_title(name, fontsize=10)
        ax.set_xlabel("w1", fontsize=8)
        ax.set_ylabel("w2", fontsize=8)
        ax.tick_params(labelsize=7)

    axes.ravel()[0].legend(loc="upper right", fontsize=6)
    plt.tight_layout(rect=(0, 0, 1, 0.96))
    plt.savefig(save_path, dpi=140)
    print(f"Saved {save_path}")


def plot_surface_grid(stats, X_train, y_train, W1, W2, Z, w_star, j_star,
                       save_path="task4_surfaces.png"):
    fig = plt.figure(figsize=(16, 14))
    fig.suptitle("Task 4: Optimizer Trajectories on 3D MSE Loss Surface")

    for i, name in enumerate(OPTIMIZER_NAMES):
        s = stats[name]
        ax = fig.add_subplot(3, 3, i + 1, projection="3d")
        ax.plot_surface(W1, W2, Z, cmap="viridis", alpha=0.55, linewidth=0, antialiased=True)

        path = subsample_path(s["weight_history"], max_points=800)
        path_z = loss_along_path(X_train, y_train, path)
        ax.plot(path[:, 0], path[:, 1], path_z, color="tab:orange", lw=1.2, zorder=5)

        ax.scatter(*s["weight_history"][0], s["path_loss"][0], color="green", s=25, label="start")
        ax.scatter(*s["weight_history"][-1], s["path_loss"][-1], color="red", s=25, label="final")
        ax.scatter(*s["lowest_w"], s["lowest_loss"], color="purple", marker="*", s=60, label="lowest loss")
        ax.scatter(*w_star, j_star, color="black", marker="x", s=45, label="J*")

        ax.set_title(name, fontsize=9)
        ax.set_xlabel("w1", fontsize=7)
        ax.set_ylabel("w2", fontsize=7)
        ax.set_zlabel("MSE", fontsize=7)
        ax.tick_params(labelsize=6)

    plt.tight_layout(rect=(0, 0, 1, 0.96))
    plt.savefig(save_path, dpi=130)
    print(f"Saved {save_path}")

def build_diagnostics_figure(stats):
    fig = plt.figure(figsize=(14, 6))
    fig.suptitle("Task 4: Per-Optimizer Diagnostics (select with RadioButtons)")

    ax_radio = fig.add_axes((0.02, 0.25, 0.13, 0.5))
    ax_loss = fig.add_axes((0.20, 0.12, 0.24, 0.75))
    ax_pred = fig.add_axes((0.50, 0.12, 0.24, 0.75))
    ax_resid = fig.add_axes((0.78, 0.12, 0.20, 0.75))

    radio = RadioButtons(ax_radio, OPTIMIZER_NAMES, active=0)

    def draw(name):
        s = stats[name]
        epochs = np.arange(1, MAX_EPOCHS + 1)

        ax_loss.clear()
        ax_loss.plot(epochs, s["epoch_loss"], color="tab:blue")
        if s["conv_epoch"] is not None:
            ax_loss.axvline(s["conv_epoch"], color="green", ls="--", lw=1,
                             label=f"converged @ {s['conv_epoch']}")
            ax_loss.legend(fontsize=7)
        ax_loss.set_xlabel("Epoch")
        ax_loss.set_ylabel("Standardized MSE")
        ax_loss.set_title("Training Loss vs Epoch", fontsize=10)
        ax_loss.grid(True, alpha=0.3)

        y_true = s["y_test_orig"]
        y_pred = s["y_test_pred_orig"]

        ax_pred.clear()
        ax_pred.scatter(y_true, y_pred, s=12, alpha=0.6, color="tab:blue")
        lims = [min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())]
        ax_pred.plot(lims, lims, color="black", lw=1, ls="--")
        ax_pred.set_xlabel("Actual MPG")
        ax_pred.set_ylabel("Predicted MPG")
        ax_pred.set_title("Actual vs Predicted MPG (test)", fontsize=10)
        ax_pred.grid(True, alpha=0.3)

        residuals = y_true - y_pred
        ax_resid.clear()
        ax_resid.scatter(y_pred, residuals, s=12, alpha=0.6, color="tab:orange")
        ax_resid.axhline(0, color="black", lw=1, ls="--")
        ax_resid.set_xlabel("Predicted MPG")
        ax_resid.set_ylabel("Residual (actual - predicted)")
        ax_resid.set_title("Residual Plot (test)", fontsize=10)
        ax_resid.grid(True, alpha=0.3)

        fig.canvas.draw_idle()

    radio.on_clicked(draw)
    draw(OPTIMIZER_NAMES[0])
    return fig, radio


# ---------------------------------------------------------------------------
# Final comparison table
# ---------------------------------------------------------------------------

def build_comparison_table(stats):
    rows = []
    for name in OPTIMIZER_NAMES:
        s = stats[name]
        rows.append({
            "Optimizer": name,
            "w1": s["w_final"][0],
            "w2": s["w_final"][1],
            "Train MSE": s["train_mse"],
            "Test MSE": s["test_mse"],
            "Test RMSE": s["test_rmse"],
            "Test R2": s["test_r2"],
            "Conv. Epoch": s["conv_epoch"] if s["conv_epoch"] is not None else "N/A",
            "#Updates": s["n_updates"],
            "Trajectory": s["behaviour_label"],
        })
    return pd.DataFrame(rows)


def main():
    X_train, X_test, y_train, y_test, x_scaler, y_scaler = prepare_data()
    results = run_all_optimizers(X_train, y_train)

    w_star = least_squares_solution(X_train, y_train)
    j_star = np.mean((y_train - X_train @ w_star) ** 2)
    print(f"Analytical optimum: w1*={w_star[0]:.4f}, w2*={w_star[1]:.4f}, J*={j_star:.6f}\n")

    stats = build_optimizer_stats(results, X_train, y_train, X_test, y_test, y_scaler, j_star)

    all_w = np.vstack([stats[n]["weight_history"] for n in OPTIMIZER_NAMES] + [w_star])
    margin = 0.15 * (all_w.max() - all_w.min())
    w1_range = np.linspace(all_w[:, 0].min() - margin, all_w[:, 0].max() + margin, 120)
    w2_range = np.linspace(all_w[:, 1].min() - margin, all_w[:, 1].max() + margin, 120)
    W1, W2, Z = loss_surface(X_train, y_train, w1_range, w2_range)

    plot_contour_grid(stats, W1, W2, Z, w_star)
    plot_surface_grid(stats, X_train, y_train, W1, W2, Z, w_star, j_star)

    table = build_comparison_table(stats)
    pd.set_option("display.width", 140)
    pd.set_option("display.float_format", lambda v: f"{v:.4f}")
    print("\n" + "=" * 100)
    print("Final Comparison Table (metrics in original MPG scale)")
    print("=" * 100)
    print(table.to_string(index=False))
    table.to_csv("task4_comparison.csv", index=False)
    print("\nSaved task4_comparison.csv")

    fig, radio = build_diagnostics_figure(stats)
    plt.show()

    return table, stats


if __name__ == "__main__":
    main()
