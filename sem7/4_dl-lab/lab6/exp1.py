import os

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms

SEED = 42
EPOCHS = 10
BATCH_SIZE = 128
LEARNING_RATE = 0.01
MOMENTUM = 0.9
HIDDEN_SIZES = [128, 128, 128, 128, 128]
NUM_CLASSES = 10
INPUT_DIM = 784
TRAIN_SPLIT = 54000
DATA_DIR = "data"
FIG_DIR = "figures"

RUNS = [
    (1, "Zero", "zero", False),
    (2, "Small", "small", False),
    (3, "Xavier", "xavier", False),
    (4, "He", "he", False),
    (5, "Large", "large", False),
    (6, "Small", "small", True),
    (7, "He", "he", True),
    (8, "Large", "large", True),
]


class MLP(nn.Module):
    def __init__(self, use_bn):
        super().__init__()
        self.linears = nn.ModuleList()
        self.norms = nn.ModuleList()
        dim = INPUT_DIM
        for width in HIDDEN_SIZES:
            self.linears.append(nn.Linear(dim, width))
            self.norms.append(nn.BatchNorm1d(width) if use_bn else nn.Identity())
            dim = width
        self.output = nn.Linear(dim, NUM_CLASSES)
        self.relu = nn.ReLU()

    def forward(self, x, collect=False):
        activations = []
        for linear, norm in zip(self.linears, self.norms):
            x = self.relu(norm(linear(x)))
            if collect:
                activations.append(x)
        logits = self.output(x)
        if collect:
            return logits, activations
        return logits


def initialize(model, scheme):
    layers = list(model.linears) + [model.output]
    for layer in layers:
        if scheme == "zero":
            nn.init.zeros_(layer.weight)
        elif scheme == "small":
            nn.init.normal_(layer.weight, mean=0.0, std=0.01)
        elif scheme == "xavier":
            nn.init.xavier_uniform_(layer.weight)
        elif scheme == "he":
            nn.init.kaiming_normal_(layer.weight, mode="fan_in", nonlinearity="relu")
        elif scheme == "large":
            nn.init.normal_(layer.weight, mean=0.0, std=1.0)
        else:
            raise ValueError(scheme)
        nn.init.zeros_(layer.bias)


def build_loaders():
    transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,)),
            transforms.Lambda(lambda t: t.view(-1)),
        ]
    )
    full_train = datasets.MNIST(DATA_DIR, train=True, download=True, transform=transform)
    test_set = datasets.MNIST(DATA_DIR, train=False, download=True, transform=transform)
    train_set = Subset(full_train, list(range(TRAIN_SPLIT)))
    val_set = Subset(full_train, list(range(TRAIN_SPLIT, len(full_train))))
    generator = torch.Generator()
    generator.manual_seed(SEED)
    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True, generator=generator)
    val_loader = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(test_set, batch_size=BATCH_SIZE, shuffle=False)
    return train_loader, val_loader, test_loader


def evaluate(model, loader, criterion):
    model.eval()
    total_loss = 0.0
    correct = 0
    count = 0
    with torch.no_grad():
        for images, labels in loader:
            logits = model(images)
            loss = criterion(logits, labels)
            total_loss += loss.item() * labels.size(0)
            correct += (logits.argmax(dim=1) == labels).sum().item()
            count += labels.size(0)
    return total_loss / count, 100.0 * correct / count


def collect_activations(model, loader):
    model.eval()
    images, _ = next(iter(loader))
    with torch.no_grad():
        _, activations = model(images, collect=True)
    return [a.numpy().ravel() for a in activations]


def train_run(run_id, label, scheme, use_bn, loaders):
    train_loader, val_loader, test_loader = loaders
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    model = MLP(use_bn)
    initialize(model, scheme)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=LEARNING_RATE, momentum=MOMENTUM)
    initial_acts = collect_activations(model, val_loader) if scheme == "large" else None
    records = []
    num_batches = len(train_loader)
    for epoch in range(1, EPOCHS + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        count = 0
        grad_first = float("nan")
        grad_fifth = float("nan")
        for index, (images, labels) in enumerate(train_loader):
            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            if index == num_batches - 1:
                grad_first = model.linears[0].weight.grad.norm(2).item()
                grad_fifth = model.linears[4].weight.grad.norm(2).item()
            optimizer.step()
            running_loss += loss.item() * labels.size(0)
            correct += (logits.argmax(dim=1) == labels).sum().item()
            count += labels.size(0)
        train_loss = running_loss / count
        train_acc = 100.0 * correct / count
        val_loss, val_acc = evaluate(model, val_loader, criterion)
        records.append(
            {
                "run": run_id,
                "init": label,
                "bn": use_bn,
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "train_acc": train_acc,
                "val_acc": val_acc,
                "grad_norm_layer1": grad_first,
                "grad_norm_layer5": grad_fifth,
            }
        )
        print(
            f"run {run_id} {label} bn={use_bn} epoch {epoch:2d} "
            f"train_loss {train_loss:.4f} val_loss {val_loss:.4f} "
            f"train_acc {train_acc:.2f} val_acc {val_acc:.2f} "
            f"g1 {grad_first:.3e} g5 {grad_fifth:.3e}",
            flush=True,
        )
    test_loss, test_acc = evaluate(model, test_loader, criterion)
    final_acts = collect_activations(model, val_loader) if scheme == "large" else None
    return pd.DataFrame(records), test_loss, test_acc, initial_acts, final_acts


def first_epoch_at_95(frame):
    reached = frame.loc[frame["val_acc"] >= 95.0, "epoch"]
    return int(reached.iloc[0]) if len(reached) else None


def figure_one(history):
    plt.figure(figsize=(8, 5))
    for run_id in range(1, 6):
        sub = history[history["run"] == run_id]
        plt.plot(sub["epoch"], sub["train_loss"], marker="o", label=f"Run {run_id}: {sub['init'].iloc[0]}")
    plt.xlabel("Epoch")
    plt.ylabel("Training loss")
    plt.title("Training loss vs epoch without batch normalization")
    plt.yscale("log")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig1_train_loss.png"), dpi=150)
    plt.close()


def figure_two(history):
    plt.figure(figsize=(8, 5))
    for run_id in range(1, 6):
        sub = history[history["run"] == run_id]
        plt.plot(sub["epoch"], sub["val_acc"], marker="o", label=f"Run {run_id}: {sub['init'].iloc[0]}")
    plt.axhline(95.0, color="black", linestyle="--", linewidth=1, label="95% threshold")
    plt.xlabel("Epoch")
    plt.ylabel("Validation accuracy (%)")
    plt.title("Validation accuracy vs epoch without batch normalization")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig2_val_accuracy.png"), dpi=150)
    plt.close()


def figure_three(history):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    columns = ["grad_norm_layer1", "grad_norm_layer5"]
    titles = ["Hidden layer 1", "Hidden layer 5"]
    for axis, column, title in zip(axes, columns, titles):
        for run_id in range(1, 6):
            sub = history[history["run"] == run_id]
            axis.plot(sub["epoch"], sub[column], marker="o", label=f"Run {run_id}: {sub['init'].iloc[0]}")
        axis.set_xlabel("Epoch")
        axis.set_ylabel("Gradient L2 norm")
        axis.set_title(title)
        axis.set_yscale("log")
        axis.grid(True, alpha=0.3)
    axes[0].legend()
    fig.suptitle("Gradient L2 norm vs epoch without batch normalization")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig3_gradient_norms.png"), dpi=150)
    plt.close(fig)


def figure_four(history):
    pairs = [("Small", 2, 6), ("He", 4, 7), ("Large", 5, 8)]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for axis, (label, no_bn, with_bn) in zip(axes, pairs):
        a = history[history["run"] == no_bn]
        b = history[history["run"] == with_bn]
        axis.plot(a["epoch"], a["train_loss"], marker="o", label="No BN")
        axis.plot(b["epoch"], b["train_loss"], marker="s", label="BN")
        axis.set_xlabel("Epoch")
        axis.set_ylabel("Training loss")
        axis.set_title(f"{label} initialization")
        axis.set_yscale("log")
        axis.grid(True, alpha=0.3)
        axis.legend()
    fig.suptitle("Training loss with and without batch normalization")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig4_bn_comparison.png"), dpi=150)
    plt.close(fig)


def draw_histogram(axis, values, color, title):
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        axis.text(
            0.5,
            0.5,
            "all activations are\nnot a number",
            ha="center",
            va="center",
            transform=axis.transAxes,
        )
    else:
        axis.hist(finite, bins=80, color=color)
        axis.set_yscale("log")
    axis.set_xlabel("Activation value")
    axis.set_ylabel("Count")
    axis.set_title(title)
    axis.grid(True, alpha=0.3)


def figure_five(no_bn_acts, bn_acts):
    layers = [0, 2, 4]
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for column, layer in enumerate(layers):
        for row, (acts, tag) in enumerate([(no_bn_acts, "No BN"), (bn_acts, "BN")]):
            color = "tab:blue" if row == 0 else "tab:orange"
            draw_histogram(axes[row][column], acts[layer], color, f"{tag}, hidden layer {layer + 1}")
    fig.suptitle("Activation distributions after epoch 10 for the large initialization")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig5_activations.png"), dpi=150)
    plt.close(fig)


def figure_six(no_bn_acts):
    layers = [0, 2, 4]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for column, layer in enumerate(layers):
        draw_histogram(
            axes[column],
            no_bn_acts[layer],
            "tab:blue",
            f"No BN, hidden layer {layer + 1}",
        )
        axes[column].ticklabel_format(style="sci", axis="x", scilimits=(0, 3))
    fig.suptitle("Activation distributions at initialization for the large initialization")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig6_activations_initial.png"), dpi=150)
    plt.close(fig)


def activation_stats(acts, tag):
    rows = []
    for index in [0, 2, 4]:
        values = acts[index]
        finite = values[np.isfinite(values)]
        rows.append(
            {
                "setting": tag,
                "layer": index + 1,
                "mean": float(finite.mean()) if finite.size else float("nan"),
                "std": float(finite.std()) if finite.size else float("nan"),
                "max": float(finite.max()) if finite.size else float("nan"),
                "fraction_zero": float((finite == 0).mean()) if finite.size else float("nan"),
                "fraction_finite": float(np.isfinite(values).mean()),
            }
        )
    return rows


def format_loss(value):
    return "NaN" if not np.isfinite(value) else f"{value:.4f}"


def format_norm(value):
    return "NaN" if not np.isfinite(value) else f"{value:.3e}"


def write_latex_tables(summary_frame, history, stats_frame):
    lines = []
    lines.append("\\begin{tabular}{clccccc}")
    lines.append("\\toprule")
    lines.append("Run & Initialization & BN & Final Val. Loss & Best Val. Acc. (\\%) & Epoch at 95\\% & Test Acc. (\\%) \\\\")
    lines.append("\\midrule")
    for _, row in summary_frame.iterrows():
        lines.append(
            f"{row['run']} & {row['init']} & {row['bn']} & {format_loss(row['final_val_loss'])} & "
            f"{row['best_val_acc']:.2f} & {row['epoch_95']} & {row['test_acc']:.2f} \\\\"
        )
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    with open("table_summary.tex", "w") as handle:
        handle.write("\n".join(lines) + "\n")

    lines = []
    lines.append("\\begin{tabular}{clcccc}")
    lines.append("\\toprule")
    lines.append("Run & Initialization & BN & Epoch & $\\|\\nabla W_1\\|_2$ & $\\|\\nabla W_5\\|_2$ \\\\")
    lines.append("\\midrule")
    for run_id in sorted(history["run"].unique()):
        sub = history[history["run"] == run_id]
        for epoch in [1, 5, 10]:
            row = sub[sub["epoch"] == epoch].iloc[0]
            bn = "Yes" if row["bn"] else "No"
            lines.append(
                f"{run_id} & {row['init']} & {bn} & {epoch} & "
                f"{format_norm(row['grad_norm_layer1'])} & {format_norm(row['grad_norm_layer5'])} \\\\"
            )
        lines.append("\\midrule")
    lines[-1] = "\\bottomrule"
    lines.append("\\end{tabular}")
    with open("table_gradients.tex", "w") as handle:
        handle.write("\n".join(lines) + "\n")

    lines = []
    lines.append("\\begin{tabular}{lcccccc}")
    lines.append("\\toprule")
    lines.append("Setting & Layer & Mean & Std. dev. & Max & Fraction zero & Fraction finite \\\\")
    lines.append("\\midrule")
    for _, row in stats_frame.iterrows():
        lines.append(
            f"{row['setting']} & {int(row['layer'])} & {format_norm(row['mean'])} & "
            f"{format_norm(row['std'])} & {format_norm(row['max'])} & "
            f"{format_norm(row['fraction_zero'])} & {row['fraction_finite']:.3f} \\\\"
        )
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    with open("table_activations.tex", "w") as handle:
        handle.write("\n".join(lines) + "\n")


def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    torch.manual_seed(SEED)
    loaders = build_loaders()
    frames = []
    summary = []
    activations = {}
    initial_activations = {}
    for run_id, label, scheme, use_bn in RUNS:
        frame, test_loss, test_acc, init_acts, acts = train_run(run_id, label, scheme, use_bn, loaders)
        frames.append(frame)
        if acts is not None:
            activations[run_id] = acts
            initial_activations[run_id] = init_acts
        epoch95 = first_epoch_at_95(frame)
        summary.append(
            {
                "run": run_id,
                "init": label,
                "bn": "Yes" if use_bn else "No",
                "final_val_loss": frame["val_loss"].iloc[-1],
                "best_val_acc": frame["val_acc"].max(),
                "epoch_95": epoch95 if epoch95 is not None else "NR",
                "test_acc": test_acc,
            }
        )
    history = pd.concat(frames, ignore_index=True)
    summary_frame = pd.DataFrame(summary)
    history.to_csv("history.csv", index=False)
    summary_frame.to_csv("summary.csv", index=False)
    stats = activation_stats(activations[5], "No BN") + activation_stats(activations[8], "BN")
    initial_stats = activation_stats(initial_activations[5], "No BN")
    pd.DataFrame(initial_stats).to_csv("activation_stats_initial.csv", index=False)
    stats_frame = pd.DataFrame(stats)
    stats_frame.to_csv("activation_stats.csv", index=False)
    write_latex_tables(summary_frame, history, stats_frame)
    figure_one(history)
    figure_two(history)
    figure_three(history)
    figure_four(history)
    figure_five(activations[5], activations[8])
    figure_six(initial_activations[5])
    print(summary_frame.to_string(index=False))


if __name__ == "__main__":
    main()
