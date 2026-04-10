import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import os

os.makedirs("plots", exist_ok=True)

DATA_PATH = "data.csv"

def build_rfm(path):
    df = pd.read_csv(path, encoding="latin-1")
    print(f"Loaded: {len(df):,} rows, {df['CustomerID'].nunique()} unique customers")

    df = df[df["CustomerID"].notna()]
    df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]
    df = df[df["Quantity"] > 0]
    df = df[df["UnitPrice"] > 0]

    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]

    snapshot = df["InvoiceDate"].max() + pd.Timedelta(days=1)

    rfm = df.groupby("CustomerID").agg(
        Recency=("InvoiceDate", lambda x: (snapshot - x.max()).days),
        Frequency=("InvoiceNo",  "nunique"),
        Monetary=("Revenue",    "sum"),
    ).reset_index()

    print(f"RFM shape: {rfm.shape}  |  missing values: {rfm.isnull().sum().sum()}")
    return rfm

def preprocess(rfm):
    X_raw = rfm[["Recency", "Frequency", "Monetary"]].copy()
    X_raw["Frequency"] = np.log1p(X_raw["Frequency"])
    X_raw["Monetary"]  = np.log1p(X_raw["Monetary"])
    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)
    return X

def plot_clusters(X2d, labels, title, filename, pct_var=None):
    fig, ax = plt.subplots(figsize=(7, 5))
    palette = plt.cm.tab10.colors
    for lbl in sorted(set(labels)):
        mask = labels == lbl
        color = "gray" if lbl == -1 else palette[lbl % len(palette)]
        name  = "Noise"       if lbl == -1 else f"Cluster {lbl+1}"
        ax.scatter(X2d[mask, 0], X2d[mask, 1], color=color, s=15, alpha=0.7, label=name)
    ax.set_title(title, fontsize=11)
    xlabel = f"PC 1 ({pct_var[0]:.1f}%)" if pct_var is not None else "PC 1"
    ylabel = f"PC 2 ({pct_var[1]:.1f}%)" if pct_var is not None else "PC 2"
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(fontsize=8, markerscale=1.8)
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()

if __name__ == "__main__":
    rfm = build_rfm(DATA_PATH)
    X   = preprocess(rfm)

    pca  = PCA(n_components=2, random_state=42)
    X2d  = pca.fit_transform(X)
    pct  = pca.explained_variance_ratio_ * 100

    k_range = range(2, 9)
    wcss_vals, sil_vals = [], []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        lbl = km.fit_predict(X)
        wcss_vals.append(km.inertia_)
        sil_vals.append(silhouette_score(X, lbl))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    ax1.plot(list(k_range), wcss_vals, marker="o", linewidth=2)
    ax1.set_title("Elbow Method (K-Means)")
    ax1.set_xlabel("K")
    ax1.set_ylabel("WCSS (Inertia)")
    ax1.set_xticks(list(k_range))

    ax2.plot(list(k_range), sil_vals, marker="o", color="darkorange", linewidth=2)
    ax2.set_title("Silhouette Score vs K")
    ax2.set_xlabel("K")
    ax2.set_ylabel("Silhouette Score")
    ax2.set_xticks(list(k_range))

    plt.suptitle("Optimal K Selection", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig("plots/q4_kmeans_elbow.png", dpi=150)
    plt.close()

    best_k = list(k_range)[np.argmax(sil_vals)]
    print(f"Best K by silhouette: {best_k}  (score={max(sil_vals):.4f})")

    km_final  = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    km_labels = km_final.fit_predict(X)
    km_sil    = silhouette_score(X, km_labels)
    print(f"KMeans   silhouette score: {km_sil:.4f}")

    plot_clusters(X2d, km_labels,
                  f"K-Means (k={best_k}) — Silhouette={km_sil:.3f}",
                  "plots/q4_kmeans_clusters.png", pct_var=pct)

    db        = DBSCAN(eps=1.5, min_samples=10)
    db_labels = db.fit_predict(X)
    n_db_clusters = len(set(db_labels) - {-1})
    n_noise   = np.sum(db_labels == -1)

    if n_db_clusters > 1:
        db_sil    = silhouette_score(X, db_labels)
        sil_str   = f"{db_sil:.4f}"
    else:
        db_sil  = float("nan")
        sil_str = "N/A"
    print(f"DBSCAN   silhouette score: {sil_str}  |  clusters={n_db_clusters}, noise={n_noise}")

    plot_clusters(X2d, db_labels,
                  f"DBSCAN (eps=1.5, min_s=10) — Silhouette={sil_str}\nclusters={n_db_clusters}, noise={n_noise}",
                  "plots/q4_dbscan_clusters.png", pct_var=pct)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    palette = plt.cm.tab10.colors
    for ax, labels, title in [
        (axes[0], km_labels, f"K-Means (k={best_k})\nSilhouette={km_sil:.3f}"),
        (axes[1], db_labels, f"DBSCAN (eps=1.5)\nSilhouette={sil_str}  |  noise={n_noise}"),
    ]:
        for lbl in sorted(set(labels)):
            mask  = labels == lbl
            color = "gray" if lbl == -1 else palette[lbl % len(palette)]
            name  = "Noise" if lbl == -1 else f"Cluster {lbl+1}"
            ax.scatter(X2d[mask, 0], X2d[mask, 1], color=color, s=15, alpha=0.7, label=name)
        ax.set_title(title)
        ax.set_xlabel(f"PC 1 ({pct[0]:.1f}%)")
        ax.set_ylabel(f"PC 2 ({pct[1]:.1f}%)")
        ax.legend(fontsize=8)
    plt.suptitle("Customer Segmentation — K-Means vs DBSCAN (RFM features)", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig("plots/q4_comparison.png", dpi=150)
    plt.close()

    rfm["Cluster"] = km_labels
    print("\nK-Means cluster profiles (mean RFM):")
    print(rfm.groupby("Cluster")[["Recency", "Frequency", "Monetary"]].mean().round(1).to_string())

    print("\nQ4 done. Plots saved to plots/q4_*.png")
