import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_blobs
import os

os.makedirs("plots", exist_ok=True)

def kmeans(X, k, max_iters=100, tol=1e-4):
    # Randomly initialize centroids from data points
    rng = np.random.default_rng(42)
    idx = rng.choice(len(X), k, replace=False)
    centroids = X[idx].copy()

    for _ in range(max_iters):
        # Assign each point to nearest centroid
        dists = np.linalg.norm(X[:, None] - centroids[None, :], axis=2)  # (n, k)
        labels = np.argmin(dists, axis=1)

        # Recompute centroids
        new_centroids = np.array([
            X[labels == j].mean(axis=0) if np.any(labels == j) else centroids[j]
            for j in range(k)
        ])

        # Check convergence
        if np.linalg.norm(new_centroids - centroids) < tol:
            break
        centroids = new_centroids

    return labels, centroids

def wcss(X, labels, centroids):
    total = 0.0
    for j, c in enumerate(centroids):
        pts = X[labels == j]
        total += np.sum((pts - c) ** 2)
    return total

if __name__ == "__main__":
    X, _ = make_blobs(n_samples=300, centers=4, cluster_std=0.8, random_state=42)

    K_values = [2, 3, 4, 5]
    wcss_scores = []
    colors = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple"]

    for k in K_values:
        labels, centroids = kmeans(X, k)
        score = wcss(X, labels, centroids)
        wcss_scores.append(score)

        # Plot cluster visualization
        fig, ax = plt.subplots(figsize=(6, 5))
        for j in range(k):
            pts = X[labels == j]
            ax.scatter(pts[:, 0], pts[:, 1], color=colors[j], s=20, alpha=0.7, label=f"Cluster {j+1}")
        ax.scatter(centroids[:, 0], centroids[:, 1], color="black", marker="X", s=150, zorder=5, label="Centroids")
        ax.set_title(f"K-Means (K={k})  |  WCSS={score:.2f}")
        ax.legend(fontsize=8)
        ax.set_xlabel("Feature 1")
        ax.set_ylabel("Feature 2")
        plt.tight_layout()
        plt.savefig(f"plots/q1_k{k}_clusters.png", dpi=150)
        plt.close()

    # Elbow method plot
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(K_values, wcss_scores, marker="o", linewidth=2)
    ax.set_title("Elbow Method — K vs WCSS")
    ax.set_xlabel("Number of Clusters (K)")
    ax.set_ylabel("WCSS")
    ax.set_xticks(K_values)
    plt.tight_layout()
    plt.savefig("plots/q1_elbow.png", dpi=150)
    plt.close()

    print("Q1 done. WCSS values:", dict(zip(K_values, [round(s, 2) for s in wcss_scores])))
