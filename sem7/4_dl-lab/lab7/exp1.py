import os

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from torchvision import datasets, transforms

SEED = 42
EPOCHS = 5
BATCH_SIZE = 64
LEARNING_RATE = 0.01
NUM_CLASSES = 10
TRAIN_SAMPLES = 10000
TEST_SAMPLES = 2000
TRIM_FRACTION = 0.1
PIXEL_MEAN = 0.1307
PIXEL_STD = 0.3081
INPUT_NOISE_STD = 0.1
OUTLIER_COUNT = 2
OUTLIER_FACTOR = 100.0
DATA_DIR = "data"
FIG_DIR = "figures"
TABLE_DIR = "tables"

LOSSES = ["MSE", "MedSE", "T-MSE"]
NOISE_LEVELS = [0.0, 0.1, 0.2]
BATCH_SIZES = [16, 64, 128]
COLORS = {"MSE": "#2a78d6", "MedSE": "#eb6834", "T-MSE": "#1baf7a"}
TARGET_ACC = 80.0


class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 8, 3)
        self.conv2 = nn.Conv2d(8, 16, 3)
        self.pool = nn.MaxPool2d(2)
        self.relu = nn.ReLU()
        self.fc = nn.Linear(16 * 5 * 5, NUM_CLASSES)

    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        return torch.sigmoid(self.fc(x.flatten(1)))


def squared_errors(outputs, labels):
    """Per sample squared error s_i = sum_c (y_ic - yhat_ic)^2 on one hot targets."""
    targets = torch.zeros_like(outputs)
    targets.scatter_(1, labels.unsqueeze(1), 1.0)
    return ((targets - outputs) ** 2).sum(dim=1)


def aggregate(errors, kind):
    if kind == "MSE":
        return errors.mean()
    if kind == "MedSE":
        return errors.median()
    if kind == "T-MSE":
        count = errors.numel()
        keep = count - int(TRIM_FRACTION * count)
        ordered, _ = torch.sort(errors)
        return ordered[:keep].mean()
    raise ValueError(kind)


def load_subsets():
    transform = transforms.ToTensor()
    full_train = datasets.MNIST(DATA_DIR, train=True, download=True, transform=transform)
    full_test = datasets.MNIST(DATA_DIR, train=False, download=True, transform=transform)
    generator = torch.Generator()
    generator.manual_seed(SEED)
    train_pick = torch.randperm(len(full_train), generator=generator)[:TRAIN_SAMPLES]
    test_pick = torch.randperm(len(full_test), generator=generator)[:TEST_SAMPLES]
    train_images = torch.stack([full_train[i][0] for i in train_pick.tolist()])
    train_labels = torch.tensor([full_train[i][1] for i in train_pick.tolist()])
    test_images = torch.stack([full_test[i][0] for i in test_pick.tolist()])
    test_labels = torch.tensor([full_test[i][1] for i in test_pick.tolist()])
    return train_images, train_labels, test_images, test_labels


def corrupt_labels(labels, fraction):
    if fraction == 0.0:
        return labels.clone(), 0
    generator = torch.Generator()
    generator.manual_seed(SEED)
    count = int(fraction * labels.numel())
    chosen = torch.randperm(labels.numel(), generator=generator)[:count]
    noisy = labels.clone()
    shift = torch.randint(1, NUM_CLASSES, (count,), generator=generator)
    noisy[chosen] = (labels[chosen] + shift) % NUM_CLASSES
    return noisy, count


def corrupt_images(images, fraction):
    if fraction == 0.0:
        return images.clone(), 0
    generator = torch.Generator()
    generator.manual_seed(SEED)
    count = int(fraction * images.shape[0])
    chosen = torch.randperm(images.shape[0], generator=generator)[:count]
    noisy = images.clone()
    noise = torch.randn(noisy[chosen].shape, generator=generator) * INPUT_NOISE_STD
    noisy[chosen] = noisy[chosen] + noise
    return noisy, count


def normalize(images):
    return (images - PIXEL_MEAN) / PIXEL_STD


def gradient_norm(model):
    total = 0.0
    for parameter in model.parameters():
        if parameter.grad is not None:
            total += parameter.grad.detach().norm(2).item() ** 2
    return total**0.5


def evaluate(model, images, labels, kind):
    model.eval()
    total_loss = 0.0
    correct = 0
    batches = 0
    with torch.no_grad():
        for start in range(0, images.shape[0], BATCH_SIZE):
            batch_x = images[start : start + BATCH_SIZE]
            batch_y = labels[start : start + BATCH_SIZE]
            outputs = model(batch_x)
            total_loss += aggregate(squared_errors(outputs, batch_y), kind).item()
            correct += (outputs.argmax(dim=1) == batch_y).sum().item()
            batches += 1
    return total_loss / batches, 100.0 * correct / labels.numel()


def train(kind, train_x, train_y, test_x, test_y, batch_size=BATCH_SIZE, tag=""):
    torch.manual_seed(SEED)
    model = CNN()
    optimizer = torch.optim.SGD(model.parameters(), lr=LEARNING_RATE)
    generator = torch.Generator()
    generator.manual_seed(SEED)
    loader = DataLoader(
        TensorDataset(train_x, train_y),
        batch_size=batch_size,
        shuffle=True,
        generator=generator,
    )
    history = []
    for epoch in range(1, EPOCHS + 1):
        model.train()
        running_loss = 0.0
        running_grad = 0.0
        correct = 0
        batches = 0
        for batch_x, batch_y in loader:
            outputs = model(batch_x)
            loss = aggregate(squared_errors(outputs, batch_y), kind)
            optimizer.zero_grad()
            loss.backward()
            running_grad += gradient_norm(model)
            optimizer.step()
            running_loss += loss.item()
            correct += (outputs.argmax(dim=1) == batch_y).sum().item()
            batches += 1
        test_loss, test_acc = evaluate(model, test_x, test_y, kind)
        history.append(
            {
                "tag": tag,
                "loss_fn": kind,
                "batch_size": batch_size,
                "epoch": epoch,
                "train_loss": running_loss / batches,
                "train_acc": 100.0 * correct / train_y.numel(),
                "test_loss": test_loss,
                "test_acc": test_acc,
                "grad_norm": running_grad / batches,
            }
        )
        print(
            f"  [{tag}|{kind}|bs{batch_size}] epoch {epoch}"
            f"  train_loss {history[-1]['train_loss']:.4f}"
            f"  train_acc {history[-1]['train_acc']:.2f}"
            f"  test_loss {test_loss:.4f}"
            f"  test_acc {test_acc:.2f}"
            f"  grad {history[-1]['grad_norm']:.4f}"
        )
    return model, history


def convergence_epoch(history):
    for record in history:
        if record["test_acc"] >= TARGET_ACC:
            return record["epoch"]
    return None


def experiment_1(data):
    print("\nExperiment 1: baseline performance on clean data")
    train_x, train_y, test_x, test_y = data
    rows = []
    for kind in LOSSES:
        _, history = train(kind, normalize(train_x), train_y, normalize(test_x), test_y, tag="clean")
        rows.extend(history)
    return pd.DataFrame(rows)


def experiment_2(data):
    print("\nExperiment 2: label noise")
    train_x, train_y, test_x, test_y = data
    rows = []
    for fraction in NOISE_LEVELS[1:]:
        noisy_y, count = corrupt_labels(train_y, fraction)
        print(f" {count} of {train_y.numel()} training labels replaced")
        for kind in LOSSES:
            _, history = train(
                kind,
                normalize(train_x),
                noisy_y,
                normalize(test_x),
                test_y,
                tag=f"label{int(fraction * 100)}",
            )
            for record in history:
                record["noise_level"] = fraction
            rows.extend(history)
    return pd.DataFrame(rows)


def experiment_3(data):
    print("\nExperiment 3: input noise")
    train_x, train_y, test_x, test_y = data
    rows = []
    for fraction in NOISE_LEVELS[1:]:
        noisy_x, count = corrupt_images(train_x, fraction)
        print(f" {count} of {train_x.shape[0]} training images corrupted")
        for kind in LOSSES:
            _, history = train(
                kind,
                normalize(noisy_x),
                train_y,
                normalize(test_x),
                test_y,
                tag=f"input{int(fraction * 100)}",
            )
            for record in history:
                record["noise_level"] = fraction
            rows.extend(history)
    return pd.DataFrame(rows)


def experiment_4(data):
    print("\nExperiment 4: outlier sensitivity")
    train_x, train_y, _, _ = data
    torch.manual_seed(SEED)
    model = CNN()
    batch_x = normalize(train_x[:BATCH_SIZE])
    batch_y = train_y[:BATCH_SIZE]
    with torch.no_grad():
        clean_errors = squared_errors(model(batch_x), batch_y)
    corrupted = clean_errors.clone()
    corrupted[:OUTLIER_COUNT] *= OUTLIER_FACTOR
    rows = []
    for kind in LOSSES:
        before = aggregate(clean_errors, kind).item()
        after = aggregate(corrupted, kind).item()
        change = 100.0 * (after - before) / before
        rows.append(
            {"loss_fn": kind, "clean": before, "outlier": after, "percent_change": change}
        )
        print(f"  {kind}: {before:.6f} -> {after:.6f}  ({change:+.2f}%)")
    return pd.DataFrame(rows)


def experiment_5(data):
    print("\nExperiment 5: gradient behaviour")
    train_x, train_y, _, _ = data
    batch_x = normalize(train_x[:BATCH_SIZE])
    batch_y = train_y[:BATCH_SIZE]
    rows = []
    for kind in LOSSES:
        torch.manual_seed(SEED)
        model = CNN()
        errors = squared_errors(model(batch_x), batch_y)
        retained = errors.clone().detach().requires_grad_(True)
        aggregate(retained, kind).backward()
        weights = retained.grad
        contributing = int((weights != 0).sum().item())

        errors = squared_errors(model(batch_x), batch_y)
        loss = aggregate(errors, kind)
        model.zero_grad()
        loss.backward()
        norm = gradient_norm(model)
        rows.append(
            {
                "loss_fn": kind,
                "loss_value": loss.item(),
                "grad_norm": norm,
                "contributing_samples": contributing,
                "batch_size": BATCH_SIZE,
            }
        )
        print(
            f"  {kind}: loss {loss.item():.6f}  ||grad||_2 {norm:.6f}"
            f"  samples with nonzero dL/ds_i {contributing}/{BATCH_SIZE}"
        )

    torch.manual_seed(SEED)
    model = CNN()
    errors = squared_errors(model(batch_x), batch_y)
    median_index = int(torch.argsort(errors)[(BATCH_SIZE - 1) // 2].item())
    model.zero_grad()
    errors.median().backward(retain_graph=True)
    median_grad = torch.cat([p.grad.detach().flatten().clone() for p in model.parameters()])
    model.zero_grad()
    errors[median_index].backward()
    single_grad = torch.cat([p.grad.detach().flatten().clone() for p in model.parameters()])
    difference = (median_grad - single_grad).norm(2).item()
    print(
        f"  MedSE gradient equals the gradient of sample {median_index} alone:"
        f" ||difference||_2 = {difference:.3e}"
    )
    return pd.DataFrame(rows), median_index, difference


def experiment_6(data, baseline):
    print("\nExperiment 6: effect of batch size")
    train_x, train_y, test_x, test_y = data
    rows = []
    for batch_size in BATCH_SIZES:
        for kind in LOSSES:
            if batch_size == BATCH_SIZE:
                history = baseline[baseline["loss_fn"] == kind].to_dict("records")
            else:
                _, history = train(
                    kind,
                    normalize(train_x),
                    train_y,
                    normalize(test_x),
                    test_y,
                    batch_size=batch_size,
                    tag=f"bs{batch_size}",
                )
            rows.extend(history)
    return pd.DataFrame(rows)


def plot_accuracy(baseline):
    plt.figure(figsize=(7, 4.5))
    for kind in LOSSES:
        sub = baseline[baseline["loss_fn"] == kind]
        plt.plot(
            sub["epoch"],
            sub["test_acc"],
            marker="o",
            markersize=5,
            linewidth=2,
            color=COLORS[kind],
            label=kind,
        )
        plt.annotate(
            f"{sub['test_acc'].iloc[-1]:.1f}",
            (sub["epoch"].iloc[-1], sub["test_acc"].iloc[-1]),
            textcoords="offset points",
            xytext=(6, -3),
            color="#52514e",
            fontsize=9,
        )
    plt.xlabel("Epoch")
    plt.ylabel("Test accuracy (%)")
    plt.title("Test accuracy versus epoch on clean data")
    plt.xticks(range(1, EPOCHS + 1))
    plt.grid(True, alpha=0.25, linewidth=0.6)
    plt.gca().spines[["top", "right"]].set_visible(False)
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig1_accuracy.png"), dpi=200)
    plt.close()


def plot_noise(baseline, label_noise, input_noise):
    figure, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    panels = [
        (axes[0], label_noise, "Label noise"),
        (axes[1], input_noise, "Input noise"),
    ]
    for axis, frame, title in panels:
        for kind in LOSSES:
            levels = []
            accuracies = []
            for fraction in NOISE_LEVELS:
                if fraction == 0.0:
                    sub = baseline[baseline["loss_fn"] == kind]
                else:
                    sub = frame[(frame["loss_fn"] == kind) & (frame["noise_level"] == fraction)]
                levels.append(100.0 * fraction)
                accuracies.append(sub["test_acc"].iloc[-1])
            axis.plot(
                levels,
                accuracies,
                marker="o",
                markersize=6,
                linewidth=2,
                color=COLORS[kind],
                label=kind,
            )
        axis.set_xlabel("Corrupted training fraction (%)")
        axis.set_title(title)
        axis.set_xticks([100.0 * f for f in NOISE_LEVELS])
        axis.grid(True, alpha=0.25, linewidth=0.6)
        axis.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Final test accuracy (%)")
    axes[0].legend(frameon=False)
    figure.suptitle("Performance versus noise level, clean test set")
    figure.tight_layout()
    figure.savefig(os.path.join(FIG_DIR, "fig2_noise.png"), dpi=200)
    plt.close(figure)


def plot_gradient(outliers, gradients):
    figure, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    positions = range(len(LOSSES))
    changes = [outliers[outliers["loss_fn"] == k]["percent_change"].iloc[0] for k in LOSSES]
    norms = [gradients[gradients["loss_fn"] == k]["grad_norm"].iloc[0] for k in LOSSES]

    axes[0].bar(positions, changes, color=[COLORS[k] for k in LOSSES], width=0.55)
    for position, value in zip(positions, changes):
        axes[0].annotate(
            f"{value:+.1f}%",
            (position, value),
            ha="center",
            va="bottom",
            fontsize=9,
            color="#52514e",
            xytext=(0, 3),
            textcoords="offset points",
        )
    axes[0].set_ylabel("Change in aggregated loss (%)")
    axes[0].set_title(f"Sensitivity to {OUTLIER_COUNT} outliers in a batch of {BATCH_SIZE}")
    axes[0].set_ylim(0, max(changes) * 1.2)

    axes[1].bar(positions, norms, color=[COLORS[k] for k in LOSSES], width=0.55)
    for position, value in zip(positions, norms):
        axes[1].annotate(
            f"{value:.4f}",
            (position, value),
            ha="center",
            va="bottom",
            fontsize=9,
            color="#52514e",
            xytext=(0, 3),
            textcoords="offset points",
        )
    axes[1].set_ylabel(r"$\|\nabla_\theta L\|_2$")
    axes[1].set_title("Gradient norm on one batch at initialization")
    axes[1].set_ylim(0, max(norms) * 1.2)

    for axis in axes:
        axis.set_xticks(list(positions))
        axis.set_xticklabels(LOSSES)
        axis.grid(True, axis="y", alpha=0.25, linewidth=0.6)
        axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    figure.savefig(os.path.join(FIG_DIR, "fig3_outlier_gradient.png"), dpi=200)
    plt.close(figure)


def write_table(name, body):
    with open(os.path.join(TABLE_DIR, name), "w") as handle:
        handle.write(body)


def format_epoch(value):
    return "NR" if value is None else str(value)


def build_tables(baseline, label_noise, input_noise, outliers, gradients, batch_study):
    lines = ["\\begin{tabular}{lrrrrc}", "\\toprule"]
    lines.append(
        "Loss & Train loss & Train acc. (\\%) & Test loss & Test acc. (\\%)"
        " & Epoch to 80\\% \\\\"
    )
    lines.append("\\midrule")
    for kind in LOSSES:
        sub = baseline[baseline["loss_fn"] == kind]
        last = sub.iloc[-1]
        reached = convergence_epoch(sub.to_dict("records"))
        lines.append(
            f"{kind} & {last['train_loss']:.4f} & {last['train_acc']:.2f}"
            f" & {last['test_loss']:.4f} & {last['test_acc']:.2f}"
            f" & {format_epoch(reached)} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    write_table("table_baseline.tex", "\n".join(lines))

    lines = ["\\begin{tabular}{llrrr}", "\\toprule"]
    lines.append(
        "Corruption & Loss & Clean acc. (\\%) & Noisy acc. (\\%) & Degradation (pp) \\\\"
    )
    lines.append("\\midrule")
    for title, frame in [("Label noise", label_noise), ("Input noise", input_noise)]:
        for fraction in NOISE_LEVELS[1:]:
            for kind in LOSSES:
                clean = baseline[baseline["loss_fn"] == kind]["test_acc"].iloc[-1]
                sub = frame[(frame["loss_fn"] == kind) & (frame["noise_level"] == fraction)]
                noisy = sub["test_acc"].iloc[-1]
                lines.append(
                    f"{title} {int(fraction * 100)}\\% & {kind} & {clean:.2f}"
                    f" & {noisy:.2f} & {noisy - clean:+.2f} \\\\"
                )
            lines.append("\\addlinespace")
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    write_table("table_noise.tex", "\n".join(lines))

    lines = ["\\begin{tabular}{lrrr}", "\\toprule"]
    lines.append("Loss & Clean batch loss & With 2 outliers & Change (\\%) \\\\")
    lines.append("\\midrule")
    for kind in LOSSES:
        row = outliers[outliers["loss_fn"] == kind].iloc[0]
        lines.append(
            f"{kind} & {row['clean']:.6f} & {row['outlier']:.6f}"
            f" & {row['percent_change']:+.2f} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    write_table("table_outlier.tex", "\n".join(lines))

    lines = ["\\begin{tabular}{lrrc}", "\\toprule"]
    lines.append(
        "Loss & Batch loss & $\\|\\nabla_\\theta L\\|_2$ & Samples with"
        " $\\partial L/\\partial s_i \\neq 0$ \\\\"
    )
    lines.append("\\midrule")
    for kind in LOSSES:
        row = gradients[gradients["loss_fn"] == kind].iloc[0]
        lines.append(
            f"{kind} & {row['loss_value']:.6f} & {row['grad_norm']:.6f}"
            f" & {int(row['contributing_samples'])} / {BATCH_SIZE} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    write_table("table_gradient.tex", "\n".join(lines))

    lines = ["\\begin{tabular}{rlrrc}", "\\toprule"]
    lines.append(
        "Batch & Loss & Final test acc. (\\%) & Mean $\\|\\nabla_\\theta L\\|_2$"
        " & Epoch to 80\\% \\\\"
    )
    lines.append("\\midrule")
    for batch_size in BATCH_SIZES:
        for kind in LOSSES:
            sub = batch_study[
                (batch_study["loss_fn"] == kind) & (batch_study["batch_size"] == batch_size)
            ]
            last = sub.iloc[-1]
            reached = convergence_epoch(sub.to_dict("records"))
            lines.append(
                f"{batch_size} & {kind} & {last['test_acc']:.2f}"
                f" & {sub['grad_norm'].mean():.4f} & {format_epoch(reached)} \\\\"
            )
        lines.append("\\addlinespace")
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    write_table("table_batch.tex", "\n".join(lines))

    lines = ["\\begin{tabular}{lccc}", "\\toprule"]
    lines.append("Quantity & MSE & MedSE & T-MSE \\\\")
    lines.append("\\midrule")

    def row(title, values, fmt="{:.2f}"):
        cells = " & ".join(fmt.format(v) if not isinstance(v, str) else v for v in values)
        lines.append(f"{title} & {cells} \\\\")

    row(
        "Clean test accuracy (\\%)",
        [baseline[baseline["loss_fn"] == k]["test_acc"].iloc[-1] for k in LOSSES],
    )
    for title, frame in [("Label", label_noise), ("Input", input_noise)]:
        for fraction in NOISE_LEVELS[1:]:
            clean = [baseline[baseline["loss_fn"] == k]["test_acc"].iloc[-1] for k in LOSSES]
            noisy = [
                frame[(frame["loss_fn"] == k) & (frame["noise_level"] == fraction)][
                    "test_acc"
                ].iloc[-1]
                for k in LOSSES
            ]
            row(
                f"{title} noise {int(fraction * 100)}\\% degradation (pp)",
                [n - c for n, c in zip(noisy, clean)],
                "{:+.2f}",
            )
    row(
        "Epoch reaching 80\\% test accuracy",
        [
            format_epoch(
                convergence_epoch(baseline[baseline["loss_fn"] == k].to_dict("records"))
            )
            for k in LOSSES
        ],
    )
    row(
        "Outlier sensitivity (\\% change)",
        [outliers[outliers["loss_fn"] == k]["percent_change"].iloc[0] for k in LOSSES],
        "{:+.2f}",
    )
    row(
        "$\\|\\nabla_\\theta L\\|_2$ at initialization",
        [gradients[gradients["loss_fn"] == k]["grad_norm"].iloc[0] for k in LOSSES],
        "{:.5f}",
    )
    row(
        "Samples driving the gradient (of 64)",
        [str(int(gradients[gradients["loss_fn"] == k]["contributing_samples"].iloc[0])) for k in LOSSES],
    )
    for batch_size in BATCH_SIZES:
        row(
            f"Test accuracy at batch {batch_size} (\\%)",
            [
                batch_study[
                    (batch_study["loss_fn"] == k) & (batch_study["batch_size"] == batch_size)
                ]["test_acc"].iloc[-1]
                for k in LOSSES
            ],
        )
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    write_table("table_summary.tex", "\n".join(lines))


def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    os.makedirs(TABLE_DIR, exist_ok=True)
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    data = load_subsets()
    print(
        f"Training samples {data[0].shape[0]}, test samples {data[2].shape[0]},"
        f" trimmed count at batch {BATCH_SIZE} is {int(TRIM_FRACTION * BATCH_SIZE)}"
    )

    baseline = experiment_1(data)
    label_noise = experiment_2(data)
    input_noise = experiment_3(data)
    outliers = experiment_4(data)
    gradients, median_index, difference = experiment_5(data)
    batch_study = experiment_6(data, baseline)

    baseline.to_csv("history_clean.csv", index=False)
    label_noise.to_csv("history_label_noise.csv", index=False)
    input_noise.to_csv("history_input_noise.csv", index=False)
    outliers.to_csv("outlier_sensitivity.csv", index=False)
    gradients.to_csv("gradient_behaviour.csv", index=False)
    batch_study.to_csv("history_batch_size.csv", index=False)

    plot_accuracy(baseline)
    plot_noise(baseline, label_noise, input_noise)
    plot_gradient(outliers, gradients)
    build_tables(baseline, label_noise, input_noise, outliers, gradients, batch_study)

    with open(os.path.join(TABLE_DIR, "median_fact.tex"), "w") as handle:
        handle.write(
            f"sample index {median_index} of the batch, with"
            f" $\\|\\nabla_\\theta L_{{\\mathrm{{MedSE}}}} -"
            f" \\nabla_\\theta s_{{{median_index}}}\\|_2 ="
            f" {'0' if difference == 0.0 else format(difference, '.1e')}$"
        )
    print("\nFigures, tables and CSV files written.")


if __name__ == "__main__":
    main()
