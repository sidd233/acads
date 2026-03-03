# ==============================================================================
# Effect of Class Priors in Gaussian Classification
# ==============================================================================

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Create output directory for plots
os.makedirs("plots", exist_ok=True)

np.random.seed(42)

# ── Dataset Generation ──────────────────────────────────────────────────────
cov = np.array([[1.0, 0.4], [0.4, 1.5]])
mean1 = np.array([1.0, 1.0])
mean2 = np.array([4.0, 4.0])

X_c1 = np.random.multivariate_normal(mean1, cov, 400)
X_c2 = np.random.multivariate_normal(mean2, cov, 400)
X3   = np.vstack([X_c1, X_c2])
y3   = np.array([0]*400 + [1]*400)

idx3   = np.random.permutation(800)
split3 = int(0.7 * 800)
X3_tr, X3_te = X3[idx3[:split3]], X3[idx3[split3:]]
y3_tr, y3_te = y3[idx3[:split3]], y3[idx3[split3:]]

test_point = np.array([2.5, 2.8])

class GaussianNB:
    def __init__(self, priors=None):
        self.priors = priors  # dict {0: p0, 1: p1}

    def fit(self, X, y):
        self.classes_ = np.unique(y)
        self.means_   = {}
        self.vars_    = {}
        self.priors_  = {}
        for c in self.classes_:
            Xc = X[y == c]
            self.means_[c] = Xc.mean(axis=0)
            self.vars_[c]  = Xc.var(axis=0) + 1e-9
            if self.priors and c in self.priors:
                self.priors_[c] = self.priors[c]
            else:
                self.priors_[c] = len(Xc) / len(X)
        return self

    def _log_likelihood(self, X, c):
        mu  = self.means_[c]
        var = self.vars_[c]
        return -0.5 * np.sum(np.log(2 * np.pi * var) + (X - mu)**2 / var, axis=1)

    def predict(self, X):
        log_posts = np.column_stack([
            self._log_likelihood(X, c) + np.log(self.priors_[c])
            for c in self.classes_
        ])
        return self.classes_[np.argmax(log_posts, axis=1)]

def confusion_matrix_2(y_true, y_pred):
    tp = np.sum((y_true == 1) & (y_pred == 1))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    return np.array([[tn, fp], [fn, tp]])

def plot_boundary(ax, clf, X, y, title, test_pt):
    x_min, x_max = X[:,0].min()-1, X[:,0].max()+1
    y_min, y_max = X[:,1].min()-1, X[:,1].max()+1
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, 300),
                         np.linspace(y_min, y_max, 300))
    grid = np.c_[xx.ravel(), yy.ravel()]
    Z = clf.predict(grid).reshape(xx.shape)

    ax.contourf(xx, yy, Z, alpha=0.2, cmap="bwr", levels=[-0.5, 0.5, 1.5])
    ax.contour(xx, yy, Z, levels=[0.5], colors="black", linewidths=1.5)
    ax.scatter(X[y==0,0], X[y==0,1], s=8, label="Class 0", color="steelblue", alpha=0.5)
    ax.scatter(X[y==1,0], X[y==1,1], s=8, label="Class 1", color="tomato",    alpha=0.5)
    ax.scatter(*test_pt, s=120, color="gold", edgecolors="black", zorder=5,
               label=f"Test {test_pt}")
    ax.set_title(title)
    ax.legend(fontsize=8)
    ax.set_xlabel("x1");  ax.set_ylabel("x2")

def print_cm(cm, label):
    print(f"\n  {label}")
    print(f"  Confusion Matrix:")
    print(f"    TN={cm[0,0]}  FP={cm[0,1]}")
    print(f"    FN={cm[1,0]}  TP={cm[1,1]}")

# Equal Priors
gnb_eq = GaussianNB()
gnb_eq.fit(X3_tr, y3_tr)

pred_tr_eq = gnb_eq.predict(X3_tr)
pred_te_eq = gnb_eq.predict(X3_te)
pred_tp_eq = gnb_eq.predict(test_point.reshape(1, -1))[0]

cm_tr_eq = confusion_matrix_2(y3_tr, pred_tr_eq)
cm_te_eq = confusion_matrix_2(y3_te, pred_te_eq)
acc_tr_eq = np.mean(pred_tr_eq == y3_tr)
acc_te_eq = np.mean(pred_te_eq == y3_te)

print(f"\n  [Equal Priors] Train Acc: {acc_tr_eq:.4f} | Test Acc: {acc_te_eq:.4f}")
print(f"  Test point [2.5, 2.8] → Predicted Class: {pred_tp_eq}")
print_cm(cm_tr_eq, "Equal Priors – Train")
print_cm(cm_te_eq, "Equal Priors – Test")

# Unequal Priors 
gnb_uneq = GaussianNB(priors={0: 0.8, 1: 0.2})
gnb_uneq.fit(X3_tr, y3_tr)

pred_tr_uneq = gnb_uneq.predict(X3_tr)
pred_te_uneq = gnb_uneq.predict(X3_te)
pred_tp_uneq = gnb_uneq.predict(test_point.reshape(1, -1))[0]

cm_tr_uneq = confusion_matrix_2(y3_tr, pred_tr_uneq)
cm_te_uneq = confusion_matrix_2(y3_te, pred_te_uneq)
acc_tr_uneq = np.mean(pred_tr_uneq == y3_tr)
acc_te_uneq = np.mean(pred_te_uneq == y3_te)

print(f"\n  [Unequal Priors P(C1)=0.8, P(C2)=0.2] Train Acc: {acc_tr_uneq:.4f} | Test Acc: {acc_te_uneq:.4f}")
print(f"  Test point [2.5, 2.8] → Predicted Class: {pred_tp_uneq}")
print_cm(cm_tr_uneq, "Unequal Priors – Train")
print_cm(cm_te_uneq, "Unequal Priors – Test")

# Combined Decision Boundary Plot
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
plot_boundary(axes[0], gnb_eq,   X3, y3, "Q3 – Equal Priors (0.5 / 0.5)",         test_point)
plot_boundary(axes[1], gnb_uneq, X3, y3, "Q3 – Unequal Priors (0.8 / 0.2)",       test_point)
plt.suptitle("Gaussian Naive Bayes – Decision Boundaries", fontsize=12, fontweight="bold")
plt.tight_layout()
plt.savefig("plots/q3_decision_boundaries.png", dpi=150)
plt.close()

# Confusion-matrix heatmaps
def plot_cm(ax, cm, title):
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0,1]);  ax.set_yticks([0,1])
    ax.set_xticklabels(["Pred 0","Pred 1"])
    ax.set_yticklabels(["Actual 0","Actual 1"])
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i,j]), ha="center", va="center",
                    color="black", fontsize=14, fontweight="bold")
    ax.set_title(title, fontsize=10)

fig, axes = plt.subplots(2, 2, figsize=(9, 7))
plot_cm(axes[0,0], cm_tr_eq,   "Equal Priors – Train CM")
plot_cm(axes[0,1], cm_te_eq,   "Equal Priors – Test CM")
plot_cm(axes[1,0], cm_tr_uneq, "Unequal Priors – Train CM")
plot_cm(axes[1,1], cm_te_uneq, "Unequal Priors – Test CM")
plt.suptitle("Q3 – Confusion Matrices", fontsize=12, fontweight="bold")
plt.tight_layout()
plt.savefig("plots/q3_confusion_matrices.png", dpi=150)
plt.close()

print("\n  Saved all plots in 'plots/' directory.")