import json
import pandas as pd
import matplotlib.pyplot as plt

names = {"exp1": "Baseline", "exp2": "Reduced classifier", "exp3": "Reduced width"}
colors = {"exp1": "tab:blue", "exp2": "tab:orange", "exp3": "tab:green"}
res = {k: json.load(open(f"{k}.json")) for k in names}

# ---------------- consolidated table ----------------
rows = []
for k, r in res.items():
    h = r["history"]
    rows.append({
        "Model": names[k],
        "Train acc (%)": 100 * r["final_train_acc"],
        "Val acc (%)": 100 * h["val_acc"][-1],
        "Test acc (%)": 100 * r["test_acc"],
        "Train loss": r["final_train_loss"],
        "Val loss": h["val_loss"][-1],
        "Gap (pts)": 100 * (r["final_train_acc"] - h["val_acc"][-1]),
        "Params": r["params"],
        "Time (s)": r["train_time_s"],
    })
df = pd.DataFrame(rows)
print(df.round(3).to_string(index=False))
df.round(3).to_csv("results_table.csv", index=False)
with open("results_table.tex", "w") as f:
    f.write(df.to_latex(index=False, float_format="%.2f", column_format="lrrrrrrrr"))

epochs = range(1, 11)

# ---------------- plot 1: accuracy ----------------
plt.figure(figsize=(6, 4))
for k, r in res.items():
    plt.plot(epochs, r["history"]["train_acc"], "--", color=colors[k], label=names[k] + " (train)")
    plt.plot(epochs, r["history"]["val_acc"], "-", color=colors[k], label=names[k] + " (val)")
plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.legend(fontsize=7)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("plot_accuracy.png", dpi=200)

# ---------------- plot 2: loss ----------------
plt.figure(figsize=(6, 4))
for k, r in res.items():
    plt.plot(epochs, r["history"]["train_loss"], "--", color=colors[k], label=names[k] + " (train)")
    plt.plot(epochs, r["history"]["val_loss"], "-", color=colors[k], label=names[k] + " (val)")
plt.xlabel("Epoch")
plt.ylabel("Cross-entropy loss")
plt.legend(fontsize=7)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("plot_loss.png", dpi=200)

# ---------------- plot 3: val accuracy vs parameters ----------------
plt.figure(figsize=(6, 4))
for k, r in res.items():
    plt.scatter(r["params"] / 1e6, 100 * r["history"]["val_acc"][-1], color=colors[k], s=60)
    plt.annotate(names[k], (r["params"] / 1e6, 100 * r["history"]["val_acc"][-1]),
                 textcoords="offset points", xytext=(6, 6), fontsize=8)
plt.xlabel("Trainable parameters (millions)")
plt.ylabel("Final validation accuracy (%)")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("plot_params.png", dpi=200)
