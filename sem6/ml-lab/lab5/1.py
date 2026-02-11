import pandas as pd
import numpy as np

df = pd.read_csv("mushrooms.csv")
df = df.astype("category")

for col in df.columns:
    df[col] = df[col].cat.codes

X = df.iloc[:, 1:].values
y = df.iloc[:, 0].values

classes = np.unique(y)
class_to_idx = {c: i for i, c in enumerate(classes)}

np.random.seed(0)
idx = np.random.permutation(len(X))
split = int(0.7 * len(X))

X_train, X_test = X[idx[:split]], X[idx[split:]]
y_train, y_test = y[idx[:split]], y[idx[split:]]

def train_nb(X, y, alpha=1):
    model = {}
    for c in np.unique(y):
        X_c = X[y == c]
        model[c] = {
            "prior": len(X_c) / len(X),
            "likelihood": [],
            "count": len(X_c)
        }
        for i in range(X.shape[1]):
            vals = np.unique(X[:, i])
            probs = {}
            for v in vals:
                probs[v] = (np.sum(X_c[:, i] == v) + alpha) / (
                    len(X_c) + alpha * len(vals)
                )
            model[c]["likelihood"].append(probs)
    return model

def predict_nb(model, X, alpha=1):
    preds = []
    for x in X:
        scores = {}
        for c in model:
            s = np.log(model[c]["prior"])
            for i, v in enumerate(x):
                probs = model[c]["likelihood"][i]
                if v in probs:
                    s += np.log(probs[v])
                else:
                    k = len(probs)
                    s += np.log(alpha / (model[c]["count"] + alpha * k))
            scores[c] = s
        preds.append(max(scores, key=scores.get))
    return np.array(preds)

model = train_nb(X_train, y_train)
y_pred = predict_nb(model, X_test)

accuracy = np.mean(y_pred == y_test)
print("Accuracy:", accuracy)

cm = np.zeros((len(classes), len(classes)), dtype=int)
for t, p in zip(y_test, y_pred):
    cm[class_to_idx[t]][class_to_idx[p]] += 1

print("Confusion Matrix:")
print(cm)

print("\nClassification Report:")
for c in classes:
    i = class_to_idx[c]
    TP = cm[i][i]
    FP = cm[:, i].sum() - TP
    FN = cm[i, :].sum() - TP
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    support = cm[i, :].sum()
    print(f"Class {c}: Precision={precision:.4f}, Recall={recall:.4f}, F1={f1:.4f}, Support={support}")
