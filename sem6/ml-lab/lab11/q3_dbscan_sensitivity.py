import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_moons
from sklearn.cluster import DBSCAN
import os

os.makedirs("plots", exist_ok=True)

def classify_points(X, db):
    """Return boolean masks for core, border, and noise points."""
    core_mask = np.zeros(len(X), dtype=bool)
    core_mask[db.core_sample_indices_] = True
    noise_mask = db.labels_ == -1
    border_mask = ~core_mask & ~noise_mask
    return core_mask, border_mask, noise_mask

if __name__ == "__main__":
    X, _ = make_moons(n_samples=300, noise=0.1, random_state=42)

    eps_values = [0.1, 0.2, 0.4]
    min_samples_values = [3, 5, 10]

    fig, axes = plt.subplots(
        len(eps_values), len(min_samples_values),
        figsize=(14, 12)
    )

    palette = plt.cm.tab10.colors

    for i, eps in enumerate(eps_values):
        for j, ms in enumerate(min_samples_values):
            ax = axes[i][j]
            db = DBSCAN(eps=eps, min_samples=ms).fit(X)
            labels = db.labels_
            core_mask, border_mask, noise_mask = classify_points(X, db)

            unique_labels = set(labels) - {-1}
            n_clusters = len(unique_labels)
            n_noise = noise_mask.sum()

            # Draw clusters
            for lbl in sorted(unique_labels):
                mask = labels == lbl
                color = palette[lbl % len(palette)]
                # Core points — filled
                ax.scatter(X[mask & core_mask, 0], X[mask & core_mask, 1],
                           color=color, s=25, alpha=0.9)
                # Border points — hollow marker
                ax.scatter(X[mask & border_mask, 0], X[mask & border_mask, 1],
                           facecolors="none", edgecolors=color, s=25, linewidths=0.8)

            # Noise points — gray X
            ax.scatter(X[noise_mask, 0], X[noise_mask, 1],
                       color="gray", marker="x", s=25, linewidths=0.8, label="Noise")

            ax.set_title(f"eps={eps}, min_s={ms}\nclusters={n_clusters}, noise={n_noise}", fontsize=9)
            ax.set_xticks([])
            ax.set_yticks([])

            # Log point counts
            print(f"eps={eps}, min_samples={ms}: clusters={n_clusters}, "
                  f"core={core_mask.sum()}, border={border_mask.sum()}, noise={n_noise}")

    # Shared legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="steelblue", markersize=8, label="Core"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="none",
               markeredgecolor="steelblue", markersize=8, label="Border"),
        Line2D([0], [0], marker="x", color="gray", markersize=8, label="Noise"),
    ]
    fig.legend(handles=legend_elements, loc="lower center", ncol=3, fontsize=10, frameon=True)
    fig.suptitle("DBSCAN Sensitivity: eps × min_samples on make_moons", fontsize=13, fontweight="bold")
    plt.tight_layout(rect=[0, 0.04, 1, 0.97])
    plt.savefig("plots/q3_dbscan_sensitivity.png", dpi=150)
    plt.close()

    print("Q3 done. Plot saved to plots/q3_dbscan_sensitivity.png")
