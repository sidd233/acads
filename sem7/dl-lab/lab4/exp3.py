import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons

from exp1 import prepare_data
from optimizers import run_all_optimizers, MAX_EPOCHS

OPTIMIZER_NAMES = [
    "BGD", "MBGD", "Momentum GD", "SGD", "SGD with Momentum",
    "NAG", "Nesterov SGD", "AdaGrad", "RMSProp",
]


def print_summary(results):
    print(f"{'Optimizer':<20}{'Final w1':>10}{'Final w2':>10}"
          f"{'Final loss':>14}{'#Updates':>12}")
    print("-" * 66)
    for name in OPTIMIZER_NAMES:
        r = results[name]
        print(f"{name:<20}{r['w_final'][0]:>10.4f}{r['w_final'][1]:>10.4f}"
              f"{r['epoch_loss'][-1]:>14.4f}{r['n_updates']:>12d}")


def main():
    X_train, _X_test, y_train, _y_test, _x_scaler, _y_scaler = prepare_data()
    results = run_all_optimizers(X_train, y_train)

    print_summary(results)

    fig = plt.figure(figsize=(12, 6))
    fig.suptitle("Task 3: Optimizer Comparison (select with RadioButtons)")

    ax_radio = fig.add_axes((0.02, 0.25, 0.16, 0.5))
    ax_loss = fig.add_axes((0.26, 0.12, 0.33, 0.75))
    ax_traj = fig.add_axes((0.65, 0.12, 0.32, 0.75))

    radio = RadioButtons(ax_radio, OPTIMIZER_NAMES, active=0)

    def draw(name):
        r = results[name]
        epochs = np.arange(1, MAX_EPOCHS + 1)

        ax_loss.clear()
        ax_loss.plot(epochs, r["epoch_loss"], color="tab:blue")
        ax_loss.set_xlabel("Epoch")
        ax_loss.set_ylabel("Full-training-set MSE")
        ax_loss.set_title(f"{name}: Training Loss")
        ax_loss.grid(True, alpha=0.3)

        wh = r["weight_history"]
        ax_traj.clear()
        ax_traj.plot(wh[:, 0], wh[:, 1], color="tab:orange", lw=1, alpha=0.8)
        ax_traj.scatter(*wh[0], color="green", zorder=5, label="start")
        ax_traj.scatter(*wh[-1], color="red", zorder=5, label="end")
        ax_traj.set_xlabel("w1")
        ax_traj.set_ylabel("w2")
        ax_traj.set_title(f"{name}: Weight Trajectory ({r['n_updates']} updates)")
        ax_traj.legend(loc="best", fontsize=8)
        ax_traj.grid(True, alpha=0.3)

        fig.canvas.draw_idle()

    radio.on_clicked(draw)
    draw(OPTIMIZER_NAMES[0])

    plt.show()


if __name__ == "__main__":
    main()
