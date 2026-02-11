import pandas as pd
import numpy as np

url = "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data"
cols = ['sl','sw','pl','pw','class']
df = pd.read_csv(url, names=cols)

X = df.iloc[:, :-1].values
y = df.iloc[:, -1].astype('category').cat.codes.values
classes = np.unique(y)
class_to_idx = {c: i for i, c in enumerate(classes)}

def train_gnb(X, y):
    model = {}
    for c in np.unique(y):
        X_c = X[y == c]
        model[c] = {
            'mean': X_c.mean(axis=0),
            'var': X_c.var(axis=0),
            'prior': len(X_c) / len(X)
        }
    return model

def gaussian_pdf(x, mean, var):
    return np.exp(-(x-mean)**2 / (2*var)) / np.sqrt(2*np.pi*var)

def predict_gnb(model, X):
    preds = []
    for x in X:
        scores = {}
        for c in model:
            s = np.log(model[c]['prior'])
            s += np.sum(np.log(gaussian_pdf(x, model[c]['mean'], model[c]['var'])))
            scores[c] = s
        preds.append(max(scores, key=scores.get))
    return np.array(preds)

def evaluate(y_true, y_pred):
    acc = np.mean(y_true == y_pred)
    cm = np.zeros((len(classes), len(classes)), dtype=int)
    for t, p in zip(y_true, y_pred):
        cm[class_to_idx[t]][class_to_idx[p]] += 1
    print("Accuracy:", acc)
    print("Confusion Matrix:")
    print(cm)
    print("Classification Report:")
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

for seed in [0, 1, 2]:
    np.random.seed(seed)
    idx = np.random.permutation(len(X))
    split = int(0.7 * len(X))
    X_train, X_test = X[idx[:split]], X[idx[split:]]
    y_train, y_test = y[idx[:split]], y[idx[split:]]
    model = train_gnb(X_train, y_train)
    y_pred = predict_gnb(model, X_test)
    print("\nRandom Seed:", seed)
    evaluate(y_test, y_pred)
