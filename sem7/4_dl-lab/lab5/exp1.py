import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 42
LR = 0.001
MOMENTUM = 0.8
BATCH_SIZE = 32
SUP_EPOCHS = 30
PRETRAIN_EPOCHS = 20
TEST_SIZE = 0.2
HIDDEN = [3, 3, 3, 3]
DATA_PATH = "Social_Network_Ads.csv"
EPS = 1e-12

def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -60.0, 60.0)))


class StandardScaler:
    def fit(self, X):
        self.mean_ = X.mean(axis=0)
        self.std_ = X.std(axis=0, ddof=0)
        self.std_[self.std_ == 0] = 1.0
        return self

    def transform(self, X):
        return (X - self.mean_) / self.std_

    def fit_transform(self, X):
        return self.fit(X).transform(X)


def stratified_train_test_split(X, y, test_size, seed):
    rng = np.random.RandomState(seed)
    y_flat = y.ravel()
    train_idx, test_idx = [], []
    for cls in np.unique(y_flat):
        idx = np.where(y_flat == cls)[0]
        rng.shuffle(idx)
        n_test = int(round(len(idx) * test_size))
        test_idx.extend(idx[:n_test])
        train_idx.extend(idx[n_test:])
    train_idx = np.array(train_idx)
    test_idx = np.array(test_idx)
    rng.shuffle(train_idx)
    rng.shuffle(test_idx)
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


def load_data():
    df = pd.read_csv(DATA_PATH)
    df["Gender"] = (df["Gender"] == "Male").astype(float)  # Female=0, Male=1
    X = df[["Gender", "Age", "EstimatedSalary"]].to_numpy(dtype=float)
    y = df["Purchased"].to_numpy(dtype=float).reshape(-1, 1)

    X_train, X_test, y_train, y_test = stratified_train_test_split(
        X, y, TEST_SIZE, SEED
    )
    scaler = StandardScaler().fit(X_train)
    return scaler.transform(X_train), scaler.transform(X_test), y_train, y_test

class Dense:
    def __init__(self, n_in, n_out, activation, rng):
        self.W = rng.uniform(-0.5, 0.5, size=(n_in, n_out))
        self.b = np.zeros(n_out)
        self.activation = activation
        self.vW = np.zeros_like(self.W)
        self.vb = np.zeros_like(self.b)
        self.frozen = False

    def forward(self, x):
        self.x = x
        self.z = x @ self.W + self.b
        self.a = sigmoid(self.z) if self.activation == "sigmoid" else self.z
        return self.a

    def backward(self, da):
        if self.activation == "sigmoid":
            dz = da * self.a * (1.0 - self.a)
        else:  # linear
            dz = da
        self.dW = self.x.T @ dz
        self.db = dz.sum(axis=0)
        return dz @ self.W.T

    def step(self):
        if self.frozen:
            return
        self.vW = MOMENTUM * self.vW - LR * self.dW
        self.vb = MOMENTUM * self.vb - LR * self.db
        self.W += self.vW
        self.b += self.vb


def net_forward(layers, x):
    for layer in layers:
        x = layer.forward(x)
    return x


def net_backward(layers, grad):
    for layer in reversed(layers):
        grad = layer.backward(grad)


def net_step(layers):
    for layer in layers:
        layer.step()

def bce_loss(p, y):
    p = np.clip(p, EPS, 1.0 - EPS)
    return float(np.mean(-(y * np.log(p) + (1.0 - y) * np.log(1.0 - p))))


def bce_grad(p, y):
    """dL/dp for the mean BCE; equals (p - y) / (p(1-p)) / N."""
    n = len(y)
    p = np.clip(p, EPS, 1.0 - EPS)
    return (p - y) / (p * (1.0 - p) * n)


def mse_loss(pred, target):
    return float(np.mean((pred - target) ** 2))


def mse_grad(pred, target):
    return 2.0 * (pred - target) / pred.size


def accuracy(p, y):
    return float(np.mean((p >= 0.5) == (y >= 0.5)))

def train_supervised(layers, X_train, y_train, X_test, y_test, epochs, rng):
    history = {k: [] for k in ("train_loss", "test_loss", "train_acc", "test_acc")}
    n = len(X_train)
    for _ in range(epochs):
        order = rng.permutation(n)
        for start in range(0, n, BATCH_SIZE):
            batch = order[start:start + BATCH_SIZE]
            xb, yb = X_train[batch], y_train[batch]
            pred = net_forward(layers, xb)
            net_backward(layers, bce_grad(pred, yb))
            net_step(layers)

        p_train = net_forward(layers, X_train)
        p_test = net_forward(layers, X_test)
        history["train_loss"].append(bce_loss(p_train, y_train))
        history["test_loss"].append(bce_loss(p_test, y_test))
        history["train_acc"].append(accuracy(p_train, y_train))
        history["test_acc"].append(accuracy(p_test, y_test))
    return history


def pretrain_layer(representation, rng, epochs):
    dim = representation.shape[1]
    encoder = Dense(dim, 3, "sigmoid", rng)
    decoder = Dense(3, dim, "linear", rng)
    layers = [encoder, decoder]
    n = len(representation)
    losses = []
    for _ in range(epochs):
        order = rng.permutation(n)
        for start in range(0, n, BATCH_SIZE):
            batch = order[start:start + BATCH_SIZE]
            xb = representation[batch]
            out = net_forward(layers, xb)
            net_backward(layers, mse_grad(out, xb))
            net_step(layers)
        losses.append(mse_loss(net_forward(layers, representation), representation))
    return encoder, losses

def build_full_network(rng):
    layers = []
    n_in = 3
    for n_out in HIDDEN:
        layers.append(Dense(n_in, n_out, "sigmoid", rng))
        n_in = n_out
    layers.append(Dense(n_in, 1, "sigmoid", rng))  # output layer
    return layers


def run_case1(X_train, y_train, X_test, y_test):
    rng = np.random.default_rng(SEED)
    layers = build_full_network(rng)
    return train_supervised(
        layers, X_train, y_train, X_test, y_test, SUP_EPOCHS, rng
    )


def run_case2(X_train, y_train, X_test, y_test):
    rng = np.random.default_rng(SEED)

    representation = X_train.copy()
    encoders, pretrain_losses = [], []
    for stage in range(len(HIDDEN)):
        encoder, losses = pretrain_layer(representation, rng, PRETRAIN_EPOCHS)
        encoders.append(encoder)
        pretrain_losses.append(losses)
        representation = encoder.forward(representation)  # freeze -> next stage
        print(
            f"  pre-train stage {stage + 1} "
            f"(H{stage} -> H{stage + 1}): MSE {losses[0]:.4f} -> {losses[-1]:.4f}"
        )

    rng = np.random.default_rng(SEED + 1)
    layers = []
    for encoder in encoders:
        layer = Dense(3, 3, "sigmoid", rng)
        layer.W = encoder.W.copy()
        layer.b = encoder.b.copy()
        layers.append(layer)
    layers.append(Dense(3, 1, "sigmoid", rng))

    for layer in layers:
        layer.frozen = False

    history = train_supervised(
        layers, X_train, y_train, X_test, y_test, SUP_EPOCHS, rng
    )
    history["pretrain_losses"] = pretrain_losses
    return history

def plot_case(history, title, path):
    epochs = range(1, SUP_EPOCHS + 1)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    axes[0].plot(epochs, history["train_loss"], label="train")
    axes[0].plot(epochs, history["test_loss"], label="test")
    axes[0].set_xlabel("epoch")
    axes[0].set_ylabel("BCE loss")
    axes[0].set_title("Loss")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    axes[1].plot(epochs, history["train_acc"], label="train")
    axes[1].plot(epochs, history["test_acc"], label="test")
    axes[1].set_xlabel("epoch")
    axes[1].set_ylabel("accuracy")
    axes[1].set_title("Accuracy")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_comparison(h1, h2, path):
    epochs = range(1, SUP_EPOCHS + 1)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    axes[0].plot(epochs, h1["test_loss"], label="no pre-training")
    axes[0].plot(epochs, h2["test_loss"], label="with pre-training")
    axes[0].set_xlabel("epoch")
    axes[0].set_ylabel("test BCE loss")
    axes[0].set_title("Test loss")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    axes[1].plot(epochs, h1["test_acc"], label="no pre-training")
    axes[1].plot(epochs, h2["test_acc"], label="with pre-training")
    axes[1].set_xlabel("epoch")
    axes[1].set_ylabel("test accuracy")
    axes[1].set_title("Test accuracy")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    fig.suptitle("Case 1 vs Case 2")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)

def main():
    np.random.seed(SEED)
    X_train, X_test, y_train, y_test = load_data()
    print(
        f"train {X_train.shape[0]} samples "
        f"(pos rate {y_train.mean():.3f}), "
        f"test {X_test.shape[0]} samples (pos rate {y_test.mean():.3f})"
    )

    print("\nCase 1 - without pre-training")
    hist1 = run_case1(X_train, y_train, X_test, y_test)
    plot_case(hist1, "Case 1 - without pre-training", "case1.png")

    print("\nCase 2 - with greedy layer-wise pre-training")
    hist2 = run_case2(X_train, y_train, X_test, y_test)
    plot_case(hist2, "Case 2 - with pre-training", "case2.png")

    plot_comparison(hist1, hist2, "case_comparison.png")

    print("\nFinal results (epoch 30)")
    print(f"{'':22s}{'train loss':>12s}{'test loss':>12s}"
          f"{'train acc':>12s}{'test acc':>12s}")
    for name, h in (("Case 1 (no pre-train)", hist1),
                    ("Case 2 (pre-trained)", hist2)):
        print(f"{name:22s}{h['train_loss'][-1]:>12.4f}{h['test_loss'][-1]:>12.4f}"
              f"{h['train_acc'][-1]:>12.4f}{h['test_acc'][-1]:>12.4f}")
    print("\nsaved: case1.png, case2.png, case_comparison.png")


if __name__ == "__main__":
    main()
