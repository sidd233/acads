import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_moons
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score
import os

os.makedirs("plots", exist_ok=True)

if __name__ == "__main__":
    X, _ = make_moons(n_samples=300, noise=0.08, random_state=42)

    # --- K-Means ---
    km = KMeans(n_clusters=2, random_state=42, n_init=10)
    km_labels = km.fit_predict(X)

    # --- DBSCAN ---
    db = DBSCAN(eps=0.2, min_samples=5)
    db_labels = db.fit_predict(X)

    # Silhouette scores (only when more than 1 cluster and no all-noise)
    km_sil = silhouette_score(X, km_labels)
    db_unique = set(db_labels) - {-1}
    db_sil = silhouette_score(X, db_labels) if len(db_unique) > 1 else float("nan")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # K-Means plot
    ax = axes[0]
    for lbl in np.unique(km_labels):
        ax.scatter(X[km_labels == lbl, 0], X[km_labels == lbl, 1], s=20, alpha=0.8, label=f"Cluster {lbl+1}")
    ax.scatter(km.cluster_centers_[:, 0], km.cluster_centers_[:, 1],
               color="black", marker="X", s=150, zorder=5, label="Centroids")
    ax.set_title(f"K-Means (k=2)\nSilhouette={km_sil:.3f}")
    ax.legend(fontsize=8)
    ax.set_xlabel("Feature 1")
    ax.set_ylabel("Feature 2")

    # DBSCAN plot
    ax = axes[1]
    palette = plt.cm.tab10.colors
    for lbl in sorted(np.unique(db_labels)):
        mask = db_labels == lbl
        color = "gray" if lbl == -1 else palette[lbl % len(palette)]
        label = "Noise" if lbl == -1 else f"Cluster {lbl+1}"
        ax.scatter(X[mask, 0], X[mask, 1], color=color, s=20, alpha=0.8, label=label)
    sil_str = f"{db_sil:.3f}" if not np.isnan(db_sil) else "N/A"
    ax.set_title(f"DBSCAN (eps=0.2, min_samples=5)\nSilhouette={sil_str}")
    ax.legend(fontsize=8)
    ax.set_xlabel("Feature 1")
    ax.set_ylabel("Feature 2")

    plt.suptitle("K-Means vs DBSCAN on make_moons", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig("plots/q2_kmeans_vs_dbscan.png", dpi=150)
    plt.close()

    print(f"Q2 done. KMeans silhouette={km_sil:.3f}, DBSCAN silhouette={sil_str}")
    print(f"DBSCAN clusters found: {len(db_unique)}, noise points: {np.sum(db_labels == -1)}")
