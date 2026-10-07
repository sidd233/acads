import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 42
LR = 0.001
MOMENTUM = 0.8
BATCH_SIZE = 16
EPOCHS = 30
BASE_ARCH = [16, 32, 16, 26]
L2_LAMBDA = 0.001
INPUT_NOISE_SIGMA = 0.1
INPUT_NOISE_CLIP = 1.0
LABEL_NOISE_FRAC = 0.10
ES_PATIENCE = 5
ES_MIN_DELTA = 0.001
DROPOUT = {0: 0.5, 1: 0.2}
DATA_PATH = "letter_recognition/letter-recognition.data"
EPS = 1e-12

def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -60.0, 60.0)))


def softmax(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def scce_loss(probs, y):
    return float(np.mean(-np.log(np.clip(probs[np.arange(len(y)), y], EPS, 1.0))))


def scce_grad(probs, y):
    grad = probs.copy()
    grad[np.arange(len(y)), y] -= 1.0
    return grad / len(y)


def accuracy(probs, y):
    return float(np.mean(np.argmax(probs, axis=1) == y))


def truncated_normal(std, size, clip, rng):
    out = rng.normal(0.0, std, size)
    bad = np.abs(out) > clip
    while bad.any():
        out[bad] = rng.normal(0.0, std, int(bad.sum()))
        bad = np.abs(out) > clip
    return out


class StandardScaler:
    def fit(self, X):
        self.mean_ = X.mean(axis=0)
        self.std_ = X.std(axis=0, ddof=0)
        self.std_[self.std_ == 0] = 1.0
        return self

    def transform(self, X):
        return (X - self.mean_) / self.std_


def stratified_split_3(y, val_frac, test_frac, seed):
    rng = np.random.RandomState(seed)
    train_idx, val_idx, test_idx = [], [], []
    for cls in np.unique(y):
        idx = np.where(y == cls)[0]
        rng.shuffle(idx)
        n = len(idx)
        n_test = int(round(n * test_frac))
        n_val = int(round(n * val_frac))
        test_idx.extend(idx[:n_test])
        val_idx.extend(idx[n_test:n_test + n_val])
        train_idx.extend(idx[n_test + n_val:])
    parts = [np.array(train_idx), np.array(val_idx), np.array(test_idx)]
    for p in parts:
        rng.shuffle(p)
    return parts


def load_data():
    cols = ["lettr"] + [f"f{i}" for i in range(16)]
    df = pd.read_csv(DATA_PATH, header=None, names=cols)
    y = (df["lettr"].map(ord) - ord("A")).to_numpy()
    X = df[[f"f{i}" for i in range(16)]].to_numpy(dtype=float)

    tr, va, te = stratified_split_3(y, 0.2, 0.2, SEED)
    scaler = StandardScaler().fit(X[tr])
    return (
        scaler.transform(X[tr]), y[tr],
        scaler.transform(X[va]), y[va],
        scaler.transform(X[te]), y[te],
    )

class Dense:
    def __init__(self, n_in, n_out, activation, rng):
        self.W = rng.uniform(-0.5, 0.5, size=(n_in, n_out))
        self.b = np.zeros(n_out)
        self.activation = activation
        self.vW = np.zeros_like(self.W)
        self.vb = np.zeros_like(self.b)

    def forward(self, x):
        self.x = x
        self.z = x @ self.W + self.b
        if self.activation == "sigmoid":
            self.a = sigmoid(self.z)
        elif self.activation == "softmax":
            self.a = softmax(self.z)
        else:
            self.a = self.z
        return self.a

    def backward(self, grad):
        if self.activation == "sigmoid":
            dz = grad * self.a * (1.0 - self.a)
        else:
            dz = grad
        self.dW = self.x.T @ dz
        self.db = dz.sum(axis=0)
        return dz @ self.W.T

    def step(self, l2):
        dW = self.dW + 2.0 * l2 * self.W if l2 else self.dW
        self.vW = MOMENTUM * self.vW - LR * dW
        self.vb = MOMENTUM * self.vb - LR * self.db
        self.W += self.vW
        self.b += self.vb


def build_network(arch, rng):
    layers = []
    for i in range(len(arch) - 1):
        act = "softmax" if i == len(arch) - 2 else "sigmoid"
        layers.append(Dense(arch[i], arch[i + 1], act, rng))
    return layers


def predict(layers, x):
    for layer in layers:
        x = layer.forward(x)
    return x


def forward_dropout(layers, x, dropout, rng):
    masks = {}
    for i, layer in enumerate(layers):
        x = layer.forward(x)
        if dropout and i in dropout:
            rate = dropout[i]
            mask = (rng.random(x.shape) >= rate) / (1.0 - rate)
            x = x * mask
            masks[i] = mask
    return x, masks


def backward_dropout(layers, grad, masks):
    for i in range(len(layers) - 1, -1, -1):
        if i in masks:
            grad = grad * masks[i]
        grad = layers[i].backward(grad)


def weight_l2_norm(layers):
    return float(np.sqrt(sum(np.sum(layer.W ** 2) for layer in layers)))


def snapshot(layers):
    return [(l.W.copy(), l.b.copy()) for l in layers]


def restore(layers, snap):
    for layer, (W, b) in zip(layers, snap):
        layer.W, layer.b = W.copy(), b.copy()

def train(layers, X_train, y_train, X_val, y_val, rng,
          l2=0.0, input_noise_sigma=0.0, dropout=None, early_stopping=False):
    history = {k: [] for k in ("train_loss", "val_loss", "train_acc", "val_acc")}
    n = len(X_train)
    es = {"best_loss": np.inf, "best_epoch": 0, "stop_epoch": EPOCHS,
          "best_snapshot": None, "wait": 0}

    for epoch in range(1, EPOCHS + 1):
        order = rng.permutation(n)
        X_epoch, y_epoch = X_train[order], y_train[order]
        if input_noise_sigma:
            X_epoch = X_epoch + truncated_normal(
                input_noise_sigma, X_epoch.shape, INPUT_NOISE_CLIP, rng)

        for start in range(0, n, BATCH_SIZE):
            batch = slice(start, start + BATCH_SIZE)
            xb, yb = X_epoch[batch], y_epoch[batch]
            if dropout:
                probs, masks = forward_dropout(layers, xb, dropout, rng)
                backward_dropout(layers, scce_grad(probs, yb), masks)
            else:
                probs = predict(layers, xb)
                grad = scce_grad(probs, yb)
                for layer in reversed(layers):
                    grad = layer.backward(grad)
            for layer in layers:
                layer.step(l2)

        p_train = predict(layers, X_train)
        p_val = predict(layers, X_val)
        history["train_loss"].append(scce_loss(p_train, y_train))
        history["val_loss"].append(scce_loss(p_val, y_val))
        history["train_acc"].append(accuracy(p_train, y_train))
        history["val_acc"].append(accuracy(p_val, y_val))

        if early_stopping:
            val_loss = history["val_loss"][-1]
            if es["best_loss"] - val_loss > ES_MIN_DELTA:
                es.update(best_loss=val_loss, best_epoch=epoch, wait=0,
                          best_snapshot=snapshot(layers))
            else:
                es["wait"] += 1
                if es["wait"] >= ES_PATIENCE:
                    es["stop_epoch"] = epoch
                    break

    if early_stopping and es["best_snapshot"] is not None:
        restore(layers, es["best_snapshot"])

    return history, es


def shuffle_train(X, y, seed):
    rng = np.random.RandomState(seed)
    order = rng.permutation(len(X))
    return X[order], y[order]

def evaluate(layers, X_test, y_test):
    p = predict(layers, X_test)
    return scce_loss(p, y_test), accuracy(p, y_test), weight_l2_norm(layers)


def run_baseline(data, tag="Case 1: baseline", l2=0.0, noise=0.0, dropout=None):
    Xtr, ytr, Xva, yva, Xte, yte = data
    rng = np.random.default_rng(SEED)
    Xtr, ytr = shuffle_train(Xtr, ytr, SEED)
    layers = build_network(BASE_ARCH, rng)
    history, _ = train(layers, Xtr, ytr, Xva, yva, rng,
                       l2=l2, input_noise_sigma=noise, dropout=dropout)
    loss, acc, norm = evaluate(layers, Xte, yte)
    return dict(tag=tag, history=history, test_loss=loss, test_acc=acc,
               l2_norm=norm)


def run_label_noise(data):
    Xtr, ytr, Xva, yva, Xte, yte = data
    rng = np.random.default_rng(SEED)
    Xtr, ytr = shuffle_train(Xtr, ytr, SEED)

    ytr = ytr.copy()
    n_flip = int(LABEL_NOISE_FRAC * len(ytr))
    flip_idx = rng.choice(len(ytr), size=n_flip, replace=False)
    for i in flip_idx:
        choices = [c for c in range(26) if c != ytr[i]]
        ytr[i] = choices[rng.integers(25)]

    layers = build_network(BASE_ARCH, rng)
    history, _ = train(layers, Xtr, ytr, Xva, yva, rng)
    loss, acc, norm = evaluate(layers, Xte, yte)
    return dict(tag="Case 4: label noise (10%)", history=history,
               test_loss=loss, test_acc=acc, l2_norm=norm)


def run_early_stopping(data):
    Xtr, ytr, Xva, yva, Xte, yte = data
    rng = np.random.default_rng(SEED)
    Xtr, ytr = shuffle_train(Xtr, ytr, SEED)
    layers = build_network(BASE_ARCH, rng)
    history, es = train(layers, Xtr, ytr, Xva, yva, rng, early_stopping=True)
    loss, acc, norm = evaluate(layers, Xte, yte)
    epochs_run = len(history["val_loss"])
    return dict(tag="Case 5: early stopping", history=history,
               test_loss=loss, test_acc=acc, l2_norm=norm,
               best_epoch=es["best_epoch"], stop_epoch=es["stop_epoch"],
               epochs_saved=EPOCHS - epochs_run)


def run_ensemble(data):
    Xtr, ytr, Xva, yva, Xte, yte = data
    Xtr_s, ytr_s = shuffle_train(Xtr, ytr, SEED)
    archs = [[16, 32, 16, 26], [16, 28, 16, 26], [16, 32, 12, 26]]

    members, val_probs, test_probs = [], [], []
    for k, arch in enumerate(archs):
        rng = np.random.default_rng(SEED + k)
        layers = build_network(arch, rng)
        history, _ = train(layers, Xtr_s, ytr_s, Xva, yva, rng)
        loss, acc, norm = evaluate(layers, Xte, yte)
        members.append(dict(arch=arch, history=history, test_loss=loss,
                            test_acc=acc, l2_norm=norm))
        val_probs.append(predict(layers, Xva))
        test_probs.append(predict(layers, Xte))

    p_test = np.mean(test_probs, axis=0)
    ens = dict(tag="Case 6: ensemble (avg of 3)",
               history=None,
               test_loss=scce_loss(p_test, yte),
               test_acc=accuracy(p_test, yte),
               l2_norm=float(np.sqrt(sum(m["l2_norm"] ** 2 for m in members))),
               members=members)
    return ens

def plot_history(history, title, path):
    epochs = range(1, len(history["train_loss"]) + 1)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    axes[0].plot(epochs, history["train_loss"], label="train")
    axes[0].plot(epochs, history["val_loss"], label="validation")
    axes[0].set_xlabel("epoch")
    axes[0].set_ylabel("sparse categorical cross-entropy")
    axes[0].set_title("Loss vs epoch")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    axes[1].plot(epochs, history["train_acc"], label="train")
    axes[1].plot(epochs, history["val_acc"], label="validation")
    axes[1].set_xlabel("epoch")
    axes[1].set_ylabel("accuracy")
    axes[1].set_title("Accuracy vs epoch")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_ensemble(members, path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for m in members:
        label = "-".join(map(str, m["arch"]))
        epochs = range(1, len(m["history"]["val_loss"]) + 1)
        axes[0].plot(epochs, m["history"]["val_loss"], label=label)
        axes[1].plot(epochs, m["history"]["val_acc"], label=label)
    axes[0].set_title("Validation loss vs epoch")
    axes[0].set_xlabel("epoch")
    axes[0].set_ylabel("SCCE")
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    axes[1].set_title("Validation accuracy vs epoch")
    axes[1].set_xlabel("epoch")
    axes[1].set_ylabel("accuracy")
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    fig.suptitle("Case 6: ensemble members")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)

def main():
    np.random.seed(SEED)
    data = load_data()
    Xtr, ytr, Xva, yva, Xte, yte = data
    print(f"train {len(Xtr)}  val {len(Xva)}  test {len(Xte)}  "
          f"(features {Xtr.shape[1]}, classes {len(np.unique(ytr))})")

    results = []
    print("\nCase 1: baseline")
    results.append(run_baseline(data, "Case 1: baseline"))
    print("Case 2: L2 regularization")
    results.append(run_baseline(data, "Case 2: L2 (lambda=0.001)", l2=L2_LAMBDA))
    print("Case 3: input noise")
    results.append(run_baseline(data, "Case 3: input noise (sigma=0.1)",
                                noise=INPUT_NOISE_SIGMA))
    print("Case 4: label noise")
    results.append(run_label_noise(data))
    print("Case 5: early stopping")
    es_result = run_early_stopping(data)
    results.append(es_result)
    print("Case 6: ensemble")
    ens_result = run_ensemble(data)
    results.append(ens_result)
    print("Case 7: dropout")
    results.append(run_baseline(data, "Case 7: dropout (0.5 / 0.2)",
                                dropout=DROPOUT))

    for i, r in enumerate(results, start=1):
        if r["history"] is not None:
            plot_history(r["history"], r["tag"], f"exp2_case{i}.png")
    plot_ensemble(ens_result["members"], "exp2_case6.png")

    print("\n" + "=" * 78)
    print("Summary of all seven cases (test set)")
    print("=" * 78)
    print(f"{'case':<34}{'test loss':>12}{'test acc':>12}{'||W||_2':>14}")
    print("-" * 78)
    rows = []
    for r in results:
        print(f"{r['tag']:<34}{r['test_loss']:>12.4f}"
              f"{r['test_acc']:>12.4f}{r['l2_norm']:>14.4f}")
        rows.append((r["tag"], r["test_loss"], r["test_acc"], r["l2_norm"]))
    print("=" * 78)

    print("\nCase 5 early-stopping details:")
    print(f"  best epoch    : {es_result['best_epoch']}")
    print(f"  stopping epoch: {es_result['stop_epoch']}")
    print(f"  epochs saved  : {es_result['epochs_saved']}")

    print("\nCase 6 ensemble members:")
    for m in ens_result["members"]: # type: ignore
        arch = "-".join(map(str, m["arch"]))
        print(f"  {arch:<16} test acc {m['test_acc']:.4f}  "
              f"test loss {m['test_loss']:.4f}  ||W||_2 {m['l2_norm']:.4f}")

    pd.DataFrame(rows, columns=["case", "test_loss", "test_acc", "l2_norm"]) \
        .to_csv("exp2_summary.csv", index=False)
    print("\nsaved: exp2_case{1..7}.png, exp2_summary.csv")


if __name__ == "__main__":
    main()
