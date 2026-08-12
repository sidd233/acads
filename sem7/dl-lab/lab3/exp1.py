import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.widgets import TextBox, Button
import time

# ============================================================
# STEP 1: LOAD AND PREPROCESS DATA
# ============================================================

# Load dataset
df = pd.read_csv("faults.csv")

print("Dataset shape:", df.shape)

# ------------------------------------------------------------
# Separate features and target columns
# ------------------------------------------------------------

feature_columns = df.columns[:27].tolist()
target_columns = df.columns[27:].tolist()

X = df[feature_columns].to_numpy(dtype=float)
Y_onehot = df[target_columns].to_numpy(dtype=int)

print("X shape:", X.shape)
print("Y shape:", Y_onehot.shape)

# ------------------------------------------------------------
# Convert one-hot target to class labels
# ------------------------------------------------------------

y = np.argmax(Y_onehot, axis=1)

class_names = np.array(target_columns)

print("\nClass distribution:")
unique, counts = np.unique(y, return_counts=True)

for cls, count in zip(unique, counts):
    print(f"{cls}: {class_names[cls]} -> {count}")

# ------------------------------------------------------------
# Stratified 80/20 train-test split
# ------------------------------------------------------------

random_state = 42
rng = np.random.default_rng(random_state)

train_indices = []
test_indices = []

for cls in np.unique(y):

    cls_indices = np.where(y == cls)[0]

    rng.shuffle(cls_indices)

    n_train = int(len(cls_indices) * 0.80)

    train_indices.extend(cls_indices[:n_train])
    test_indices.extend(cls_indices[n_train:])

train_indices = np.array(train_indices)
test_indices = np.array(test_indices)

rng.shuffle(train_indices)
rng.shuffle(test_indices)

X_train = X[train_indices]
X_test = X[test_indices]

y_train = y[train_indices]
y_test = y[test_indices]

print("\nTrain shape:", X_train.shape)
print("Test shape:", X_test.shape)

# ------------------------------------------------------------
# Verify stratification
# ------------------------------------------------------------

print("\nClass distribution after split:")

for cls in np.unique(y):

    total_count = np.sum(y == cls)
    train_count = np.sum(y_train == cls)
    test_count = np.sum(y_test == cls)

    print(
        f"{class_names[cls]:15s} "
        f"Total={total_count:4d} "
        f"Train={train_count:4d} "
        f"Test={test_count:4d}"
    )

# ------------------------------------------------------------
# Z-score standardization
# ------------------------------------------------------------

# Fit scaler only on training data
mean_train = np.mean(X_train, axis=0)
std_train = np.std(X_train, axis=0)

# Prevent division by zero
std_train[std_train == 0] = 1.0

# Apply same transformation to both datasets
X_train_std = (X_train - mean_train) / std_train
X_test_std = (X_test - mean_train) / std_train

print("\nStandardized training shape:", X_train_std.shape)
print("Standardized testing shape:", X_test_std.shape)

# ------------------------------------------------------------
# Verify standardization
# ------------------------------------------------------------

print("\nMean of standardized training features:")
print(np.mean(X_train_std, axis=0))

print("\nStd of standardized training features:")
print(np.std(X_train_std, axis=0))

# ============================================================
# STEP 2: PCA
# ============================================================

# ------------------------------------------------------------
# 1. Covariance matrix
# ------------------------------------------------------------

cov_matrix = np.cov(
    X_train_std,
    rowvar=False
)

print("Covariance matrix shape:", cov_matrix.shape)

# ------------------------------------------------------------
# 2. Eigenvalues and eigenvectors
# ------------------------------------------------------------

eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)

# Sort in descending order
sorted_indices = np.argsort(eigenvalues)[::-1]

eigenvalues = eigenvalues[sorted_indices]
eigenvectors = eigenvectors[:, sorted_indices]

print("\nEigenvalues:")
print(eigenvalues)

# ------------------------------------------------------------
# 3. Explained variance ratio
# ------------------------------------------------------------

explained_variance_ratio = (
    eigenvalues / np.sum(eigenvalues)
)

explained_variance_percentage = (
    explained_variance_ratio * 100
)

print("\nExplained variance:")

for i, value in enumerate(explained_variance_percentage):
    print(f"PC{i+1:2d}: {value:.4f}%")

# ------------------------------------------------------------
# 4. Cumulative explained variance
# ------------------------------------------------------------

cumulative_explained_variance = np.cumsum(
    explained_variance_ratio
)

print("\nCumulative explained variance:")

for i, value in enumerate(
    cumulative_explained_variance * 100
):
    print(f"First {i+1:2d} PCs: {value:.4f}%")

# ------------------------------------------------------------
# 5. Find minimum number of PCs for 95%
# ------------------------------------------------------------

n_components = np.argmax(
    cumulative_explained_variance >= 0.95
) + 1

print("\n95% variance threshold:")
print("Required components:", n_components)

# ------------------------------------------------------------
# 6. Dimensionality reduction
# ------------------------------------------------------------

original_dimensions = X_train_std.shape[1]

reduction_percentage = (
    (original_dimensions - n_components)
    / original_dimensions
    * 100
)

print("Original dimensions:", original_dimensions)
print("Reduced dimensions:", n_components)
print(
    f"Dimensionality reduction: "
    f"{reduction_percentage:.2f}%"
)

# ------------------------------------------------------------
# 7. Plot cumulative explained variance
# ------------------------------------------------------------

components = np.arange(
    1,
    len(cumulative_explained_variance) + 1
)

plt.figure(figsize=(9, 5))

plt.plot(
    components,
    cumulative_explained_variance * 100,
    marker='o'
)

plt.axhline(
    y=95,
    linestyle='--',
    label='95% variance'
)

plt.axvline(
    x=n_components,
    linestyle='--',
    label=f'{n_components} components'
)

plt.xlabel("Number of Principal Components")
plt.ylabel("Cumulative Explained Variance (%)")
plt.title("Cumulative Explained Variance")
plt.grid(True)
plt.legend()

plt.show()

# ------------------------------------------------------------
# 8. Transform data using selected PCs
# ------------------------------------------------------------

principal_components = eigenvectors[:, :n_components]

X_train_pca = (
    X_train_std @ principal_components
)

X_test_pca = (
    X_test_std @ principal_components
)

print("\nPCA transformed shapes:")
print("X_train_pca:", X_train_pca.shape)
print("X_test_pca:", X_test_pca.shape)

# ------------------------------------------------------------
# 9. Original feature correlation heatmap
# ------------------------------------------------------------

correlation_original = np.corrcoef(
    X_train_std,
    rowvar=False
)

plt.figure(figsize=(10, 8))

plt.imshow(
    correlation_original,
    cmap='coolwarm',
    vmin=-1,
    vmax=1
)

plt.colorbar(label="Correlation")

plt.title(
    "Correlation Heatmap - "
    "Original Standardized Features"
)

plt.xlabel("Features")
plt.ylabel("Features")

plt.xticks(
    np.arange(27),
    np.arange(1, 28),
    rotation=90
)

plt.yticks(
    np.arange(27),
    np.arange(1, 28)
)

plt.tight_layout()
plt.show()

# ------------------------------------------------------------
# 10. PCA correlation heatmap
# ------------------------------------------------------------

correlation_pca = np.corrcoef(
    X_train_pca,
    rowvar=False
)

plt.figure(figsize=(8, 7))

plt.imshow(
    correlation_pca,
    cmap='coolwarm',
    vmin=-1,
    vmax=1
)

plt.colorbar(label="Correlation")

plt.title(
    "Correlation Heatmap - Principal Components"
)

plt.xlabel("Principal Components")
plt.ylabel("Principal Components")

plt.xticks(
    np.arange(n_components),
    np.arange(1, n_components + 1)
)

plt.yticks(
    np.arange(n_components),
    np.arange(1, n_components + 1)
)

plt.tight_layout()
plt.show()

# ------------------------------------------------------------
# 11. Verify PCA components are approximately uncorrelated
# ------------------------------------------------------------

off_diagonal = correlation_pca.copy()

np.fill_diagonal(
    off_diagonal,
    0
)

print(
    "\nMaximum absolute correlation "
    "between different PCs:",
    np.max(np.abs(off_diagonal))
)

# ------------------------------------------------------------
# 12. PC1 vs PC2
# ------------------------------------------------------------

plt.figure(figsize=(10, 7))

for cls in np.unique(y_train):

    mask = (y_train == cls)

    plt.scatter(
        X_train_pca[mask, 0],
        X_train_pca[mask, 1],
        label=class_names[cls],
        alpha=0.6
    )

plt.xlabel("Principal Component 1")
plt.ylabel("Principal Component 2")
plt.title("PC1 vs PC2 - Training Data")
plt.legend()
plt.grid(True)

plt.show()



# ============================================================
# STEP 3
# Feedforward Neural Network using NumPy
#
# Architecture:
# 27 -> 16 -> 8 -> 7
#
# Hidden activation: ReLU
# Output activation: Softmax
# Loss: Categorical Cross-Entropy
# Learning rate: 0.01
# Batch size: 32
# Epochs: 100
# Random seed: 42
# ============================================================


# ============================================================
# 1. ONE-HOT ENCODING
# ============================================================

def one_hot_encode(y, num_classes):
    one_hot = np.zeros((len(y), num_classes))

    one_hot[np.arange(len(y)), y] = 1

    return one_hot


Y_train = one_hot_encode(y_train, 7)
Y_test = one_hot_encode(y_test, 7)


# ============================================================
# 2. ACTIVATION FUNCTIONS
# ============================================================

def relu(z):
    return np.maximum(0, z)


def relu_derivative(z):
    return (z > 0).astype(float)


def softmax(z):
    # Numerical stability
    z_shifted = z - np.max(
        z,
        axis=1,
        keepdims=True
    )

    exp_z = np.exp(z_shifted)

    return exp_z / np.sum(
        exp_z,
        axis=1,
        keepdims=True
    )


# ============================================================
# 3. INITIALIZE NETWORK PARAMETERS
# ============================================================

rng = np.random.default_rng(42)

# Layer 1: 27 -> 16
W1 = rng.normal(
    0,
    0.01,
    size=(27, 16)
)

b1 = np.zeros((1, 16))


# Layer 2: 16 -> 8
W2 = rng.normal(
    0,
    0.01,
    size=(16, 8)
)

b2 = np.zeros((1, 8))


# Layer 3: 8 -> 7
W3 = rng.normal(
    0,
    0.01,
    size=(8, 7)
)

b3 = np.zeros((1, 7))


# ============================================================
# 4. FORWARD PROPAGATION
# ============================================================

def forward_pass(
    X,
    W1, b1,
    W2, b2,
    W3, b3
):

    # Hidden Layer 1
    Z1 = X @ W1 + b1
    A1 = relu(Z1)

    # Hidden Layer 2
    Z2 = A1 @ W2 + b2
    A2 = relu(Z2)

    # Output Layer
    Z3 = A2 @ W3 + b3
    Y_pred = softmax(Z3)

    # Store intermediate values
    cache = (
        X,
        Z1,
        A1,
        Z2,
        A2,
        Z3,
        Y_pred
    )

    return Y_pred, cache


# ============================================================
# 5. CATEGORICAL CROSS-ENTROPY LOSS
# ============================================================

def cross_entropy_loss(Y_true, Y_pred):

    # Prevent log(0)
    epsilon = 1e-12

    Y_pred = np.clip(
        Y_pred,
        epsilon,
        1 - epsilon
    )

    loss = -np.sum(
        Y_true * np.log(Y_pred)
    ) / len(Y_true)

    return loss


# ============================================================
# 6. BACKPROPAGATION
# ============================================================

def backward_pass(
    Y_true,
    cache,
    W2,
    W3
):

    (
        X,
        Z1,
        A1,
        Z2,
        A2,
        Z3,
        Y_pred
    ) = cache

    m = X.shape[0]


    # --------------------------------------------------------
    # Output Layer
    # --------------------------------------------------------

    # Softmax + Cross-Entropy derivative
    dZ3 = (Y_pred - Y_true) / m

    dW3 = A2.T @ dZ3

    db3 = np.sum(
        dZ3,
        axis=0,
        keepdims=True
    )


    # --------------------------------------------------------
    # Hidden Layer 2
    # --------------------------------------------------------

    dA2 = dZ3 @ W3.T

    dZ2 = (
        dA2 *
        relu_derivative(Z2)
    )

    dW2 = A1.T @ dZ2

    db2 = np.sum(
        dZ2,
        axis=0,
        keepdims=True
    )


    # --------------------------------------------------------
    # Hidden Layer 1
    # --------------------------------------------------------

    dA1 = dZ2 @ W2.T

    dZ1 = (
        dA1 *
        relu_derivative(Z1)
    )

    dW1 = X.T @ dZ1

    db1 = np.sum(
        dZ1,
        axis=0,
        keepdims=True
    )


    return (
        dW1,
        db1,
        dW2,
        db2,
        dW3,
        db3
    )


# ============================================================
# 7. UPDATE PARAMETERS
# ============================================================

def update_parameters(
    W1, b1,
    W2, b2,
    W3, b3,
    gradients,
    learning_rate
):

    (
        dW1,
        db1,
        dW2,
        db2,
        dW3,
        db3
    ) = gradients


    W1 -= learning_rate * dW1
    b1 -= learning_rate * db1

    W2 -= learning_rate * dW2
    b2 -= learning_rate * db2

    W3 -= learning_rate * dW3
    b3 -= learning_rate * db3


    return (
        W1, b1,
        W2, b2,
        W3, b3
    )


# ============================================================
# 8. PREDICTION FUNCTION
# ============================================================

def predict(
    X,
    W1, b1,
    W2, b2,
    W3, b3
):

    probabilities, _ = forward_pass(
        X,
        W1, b1,
        W2, b2,
        W3, b3
    )

    predictions = np.argmax(
        probabilities,
        axis=1
    )

    return predictions, probabilities


# ============================================================
# 9. TRAINING
# ============================================================

learning_rate = 0.01
batch_size = 32
epochs = 100

loss_history = []

num_samples = X_train_std.shape[0]

start_time = time.perf_counter()


for epoch in range(epochs):

    # --------------------------------------------------------
    # Shuffle training data
    # --------------------------------------------------------

    permutation = rng.permutation(
        num_samples
    )

    X_shuffled = X_train_std[
        permutation
    ]

    Y_shuffled = Y_train[
        permutation
    ]


    epoch_loss = 0.0
    num_batches = 0


    # --------------------------------------------------------
    # Mini-batch training
    # --------------------------------------------------------

    for start in range(
        0,
        num_samples,
        batch_size
    ):

        end = min(
            start + batch_size,
            num_samples
        )


        X_batch = X_shuffled[
            start:end
        ]

        Y_batch = Y_shuffled[
            start:end
        ]


        # ----------------------------------------------------
        # Forward propagation
        # ----------------------------------------------------

        Y_pred, cache = forward_pass(
            X_batch,
            W1, b1,
            W2, b2,
            W3, b3
        )


        # ----------------------------------------------------
        # Calculate loss
        # ----------------------------------------------------

        loss = cross_entropy_loss(
            Y_batch,
            Y_pred
        )

        epoch_loss += loss
        num_batches += 1


        # ----------------------------------------------------
        # Backpropagation
        # ----------------------------------------------------

        gradients = backward_pass(
            Y_batch,
            cache,
            W2,
            W3
        )


        # ----------------------------------------------------
        # Update weights and biases
        # ----------------------------------------------------

        (
            W1, b1,
            W2, b2,
            W3, b3
        ) = update_parameters(
            W1, b1,
            W2, b2,
            W3, b3,
            gradients,
            learning_rate
        )


    # --------------------------------------------------------
    # Average loss over all batches
    # --------------------------------------------------------

    epoch_loss /= num_batches

    loss_history.append(
        epoch_loss
    )


    # Print every 10 epochs
    if (epoch + 1) % 10 == 0:

        print(
            f"Epoch {epoch + 1:3d}/{epochs} "
            f"- Loss: {epoch_loss:.6f}"
        )


training_time = (
    time.perf_counter() - start_time
)


print(
    f"\nTraining time: "
    f"{training_time:.4f} seconds"
)


# ============================================================
# 10. TRAINING LOSS CURVE
# ============================================================

plt.figure(figsize=(8, 5))

plt.plot(
    range(1, epochs + 1),
    loss_history
)

plt.xlabel("Epoch")
plt.ylabel("Training Loss")
plt.title(
    "Training Loss - "
    "27 → 16 → 8 → 7 Neural Network"
)

plt.grid(True)

plt.show()


# ============================================================
# 11. PREDICTIONS
# ============================================================

train_predictions, train_probabilities = predict(
    X_train_std,
    W1, b1,
    W2, b2,
    W3, b3
)

test_predictions, test_probabilities = predict(
    X_test_std,
    W1, b1,
    W2, b2,
    W3, b3
)


# ============================================================
# 12. ACCURACY
# ============================================================

train_accuracy = np.mean(
    train_predictions == y_train
)

test_accuracy = np.mean(
    test_predictions == y_test
)


print(
    f"Training Accuracy: "
    f"{train_accuracy * 100:.2f}%"
)

print(
    f"Testing Accuracy: "
    f"{test_accuracy * 100:.2f}%"
)


# ============================================================
# 13. MACRO-F1 SCORE
# ============================================================

def macro_f1_score(
    y_true,
    y_pred,
    num_classes
):

    f1_scores = []


    for cls in range(num_classes):

        # True Positives
        true_positive = np.sum(
            (y_true == cls) &
            (y_pred == cls)
        )


        # False Positives
        false_positive = np.sum(
            (y_true != cls) &
            (y_pred == cls)
        )


        # False Negatives
        false_negative = np.sum(
            (y_true == cls) &
            (y_pred != cls)
        )


        # Precision
        if (
            true_positive +
            false_positive
        ) == 0:

            precision = 0.0

        else:

            precision = (
                true_positive /
                (
                    true_positive +
                    false_positive
                )
            )


        # Recall
        if (
            true_positive +
            false_negative
        ) == 0:

            recall = 0.0

        else:

            recall = (
                true_positive /
                (
                    true_positive +
                    false_negative
                )
            )


        # F1
        if precision + recall == 0:

            f1 = 0.0

        else:

            f1 = (
                2 *
                precision *
                recall /
                (precision + recall)
            )


        f1_scores.append(f1)


    return np.mean(f1_scores)


test_macro_f1 = macro_f1_score(
    y_test,
    test_predictions,
    7
)


print(
    f"Test Macro-F1: "
    f"{test_macro_f1:.4f}"
)


# ============================================================
# 14. PER-CLASS F1 SCORES
# ============================================================

def per_class_f1(
    y_true,
    y_pred,
    num_classes
):

    f1_scores = []


    for cls in range(num_classes):

        tp = np.sum(
            (y_true == cls) &
            (y_pred == cls)
        )

        fp = np.sum(
            (y_true != cls) &
            (y_pred == cls)
        )

        fn = np.sum(
            (y_true == cls) &
            (y_pred != cls)
        )


        if tp + fp == 0:
            precision = 0.0
        else:
            precision = tp / (tp + fp)


        if tp + fn == 0:
            recall = 0.0
        else:
            recall = tp / (tp + fn)


        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = (
                2 * precision * recall /
                (precision + recall)
            )


        f1_scores.append(f1)


    return np.array(f1_scores)


f1_scores = per_class_f1(
    y_test,
    test_predictions,
    7
)


print("\nPer-class F1 scores:")

for cls in range(7):

    print(
        f"{class_names[cls]:15s}: "
        f"{f1_scores[cls]:.4f}"
    )


# ============================================================
# 15. FINAL STEP 3 RESULTS
# ============================================================

print("\n" + "=" * 50)
print("STEP 3 RESULTS")
print("=" * 50)

print(
    f"Architecture       : 27 → 16 → 8 → 7"
)

print(
    f"Activation          : ReLU → ReLU → Softmax"
)

print(
    f"Learning rate       : {learning_rate}"
)

print(
    f"Batch size          : {batch_size}"
)

print(
    f"Epochs              : {epochs}"
)

print(
    f"Test Accuracy       : "
    f"{test_accuracy * 100:.2f}%"
)

print(
    f"Test Macro-F1       : "
    f"{test_macro_f1:.4f}"
)

print(
    f"Training Time       : "
    f"{training_time:.4f} seconds"
)

print("=" * 50)

# ============================================================
# STEP 4
# PCA-BASED NEURAL NETWORK
# EXPERIMENTING WITH ACTIVATION FUNCTIONS
#
# Architecture:
# d' -> 16 -> 8 -> 7
#
# Configuration A:
# ReLU -> ReLU -> Softmax
#
# Configuration B:
# ReLU -> Sigmoid -> Softmax
#
# Configuration C:
# Sigmoid -> ReLU -> Softmax
#
# Configuration D:
# Sigmoid -> Sigmoid -> Softmax
#
# Configuration E:
# Mixed:
#   Hidden Layer 1: 8 ReLU + 8 Sigmoid
#   Hidden Layer 2: 4 ReLU + 4 Sigmoid
#
# Learning rate : 0.01
# Batch size    : 32
# Epochs        : 100
# Random seed   : 42
# ============================================================


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time


# ============================================================
# 1. ONE-HOT ENCODING
# ============================================================

def one_hot_encode(y, num_classes):

    one_hot = np.zeros(
        (len(y), num_classes)
    )

    one_hot[
        np.arange(len(y)),
        y
    ] = 1

    return one_hot


Y_train = one_hot_encode(
    y_train,
    7
)

Y_test = one_hot_encode(
    y_test,
    7
)


# ============================================================
# 2. ACTIVATION FUNCTIONS
# ============================================================

def relu(z):

    return np.maximum(
        0,
        z
    )


def relu_derivative(z):

    return (
        z > 0
    ).astype(float)


def sigmoid(z):

    # Numerical stability
    z = np.clip(
        z,
        -500,
        500
    )

    return 1 / (
        1 + np.exp(-z)
    )


def sigmoid_derivative(z):

    s = sigmoid(z)

    return s * (
        1 - s
    )


def softmax(z):

    # Numerical stability
    z_shifted = (
        z -
        np.max(
            z,
            axis=1,
            keepdims=True
        )
    )

    exp_z = np.exp(
        z_shifted
    )

    return (
        exp_z /
        np.sum(
            exp_z,
            axis=1,
            keepdims=True
        )
    )


# ============================================================
# 3. GENERIC ACTIVATION FUNCTIONS
# ============================================================

def apply_activation(
    z,
    activation
):

    if activation == "relu":

        return relu(z)

    elif activation == "sigmoid":

        return sigmoid(z)

    else:

        raise ValueError(
            f"Unknown activation: {activation}"
        )


def apply_activation_derivative(
    z,
    activation
):

    if activation == "relu":

        return relu_derivative(z)

    elif activation == "sigmoid":

        return sigmoid_derivative(z)

    else:

        raise ValueError(
            f"Unknown activation: {activation}"
        )


# ============================================================
# 4. MIXED ACTIVATION
# ============================================================

def mixed_activation(
    z,
    split
):

    # First part: ReLU
    relu_part = relu(
        z[:, :split]
    )

    # Second part: Sigmoid
    sigmoid_part = sigmoid(
        z[:, split:]
    )

    return np.concatenate(
        [
            relu_part,
            sigmoid_part
        ],
        axis=1
    )


def mixed_activation_derivative(
    z,
    split
):

    # First part: ReLU derivative
    relu_part = relu_derivative(
        z[:, :split]
    )

    # Second part: Sigmoid derivative
    sigmoid_part = sigmoid_derivative(
        z[:, split:]
    )

    return np.concatenate(
        [
            relu_part,
            sigmoid_part
        ],
        axis=1
    )


# ============================================================
# 5. FORWARD PROPAGATION
# ============================================================

def forward_pass(
    X,
    W1,
    b1,
    W2,
    b2,
    W3,
    b3,
    activation1,
    activation2
):

    # --------------------------------------------------------
    # Hidden Layer 1
    # --------------------------------------------------------

    Z1 = (
        X @ W1 +
        b1
    )

    if activation1 == "mixed":

        A1 = mixed_activation(
            Z1,
            8
        )

    else:

        A1 = apply_activation(
            Z1,
            activation1
        )


    # --------------------------------------------------------
    # Hidden Layer 2
    # --------------------------------------------------------

    Z2 = (
        A1 @ W2 +
        b2
    )

    if activation2 == "mixed":

        A2 = mixed_activation(
            Z2,
            4
        )

    else:

        A2 = apply_activation(
            Z2,
            activation2
        )


    # --------------------------------------------------------
    # Output Layer
    # --------------------------------------------------------

    Z3 = (
        A2 @ W3 +
        b3
    )

    Y_pred = softmax(
        Z3
    )


    # --------------------------------------------------------
    # Cache
    # --------------------------------------------------------

    cache = (
        X,
        Z1,
        A1,
        Z2,
        A2,
        Z3,
        Y_pred
    )


    return (
        Y_pred,
        cache
    )


# ============================================================
# 6. CROSS-ENTROPY LOSS
# ============================================================

def cross_entropy_loss(
    Y_true,
    Y_pred
):

    epsilon = 1e-12

    Y_pred = np.clip(
        Y_pred,
        epsilon,
        1 - epsilon
    )

    loss = -np.sum(
        Y_true *
        np.log(Y_pred)
    ) / len(Y_true)

    return loss


# ============================================================
# 7. BACKPROPAGATION
# ============================================================

def backward_pass(
    Y_true,
    cache,
    W2,
    W3,
    activation1,
    activation2
):

    (
        X,
        Z1,
        A1,
        Z2,
        A2,
        Z3,
        Y_pred
    ) = cache


    m = X.shape[0]


    # ========================================================
    # OUTPUT LAYER
    # ========================================================

    dZ3 = (
        Y_pred -
        Y_true
    ) / m


    dW3 = (
        A2.T @ dZ3
    )


    db3 = np.sum(
        dZ3,
        axis=0,
        keepdims=True
    )


    # ========================================================
    # HIDDEN LAYER 2
    # ========================================================

    dA2 = (
        dZ3 @ W3.T
    )


    if activation2 == "mixed":

        activation2_derivative = (
            mixed_activation_derivative(
                Z2,
                4
            )
        )

    else:

        activation2_derivative = (
            apply_activation_derivative(
                Z2,
                activation2
            )
        )


    dZ2 = (
        dA2 *
        activation2_derivative
    )


    dW2 = (
        A1.T @ dZ2
    )


    db2 = np.sum(
        dZ2,
        axis=0,
        keepdims=True
    )


    # ========================================================
    # HIDDEN LAYER 1
    # ========================================================

    dA1 = (
        dZ2 @ W2.T
    )


    if activation1 == "mixed":

        activation1_derivative = (
            mixed_activation_derivative(
                Z1,
                8
            )
        )

    else:

        activation1_derivative = (
            apply_activation_derivative(
                Z1,
                activation1
            )
        )


    dZ1 = (
        dA1 *
        activation1_derivative
    )


    dW1 = (
        X.T @ dZ1
    )


    db1 = np.sum(
        dZ1,
        axis=0,
        keepdims=True
    )


    return (
        dW1,
        db1,
        dW2,
        db2,
        dW3,
        db3
    )


# ============================================================
# 8. TRAINING FUNCTION
# ============================================================

def train_network(
    X_train,
    Y_train,
    input_dim,
    activation1,
    activation2,
    learning_rate=0.01,
    batch_size=32,
    epochs=100,
    seed=42
):

    # --------------------------------------------------------
    # Random generator
    # --------------------------------------------------------

    rng = np.random.default_rng(
        seed
    )


    # --------------------------------------------------------
    # Initialize weights and biases
    # --------------------------------------------------------

    W1 = rng.normal(
        0,
        0.01,
        size=(
            input_dim,
            16
        )
    )

    b1 = np.zeros(
        (1, 16)
    )


    W2 = rng.normal(
        0,
        0.01,
        size=(
            16,
            8
        )
    )

    b2 = np.zeros(
        (1, 8)
    )


    W3 = rng.normal(
        0,
        0.01,
        size=(
            8,
            7
        )
    )

    b3 = np.zeros(
        (1, 7)
    )


    # --------------------------------------------------------
    # Loss history
    # --------------------------------------------------------

    loss_history = []


    num_samples = (
        X_train.shape[0]
    )


    # --------------------------------------------------------
    # Start timer
    # --------------------------------------------------------

    start_time = (
        time.perf_counter()
    )


    # ========================================================
    # TRAINING LOOP
    # ========================================================

    for epoch in range(
        epochs
    ):

        # ----------------------------------------------------
        # Shuffle training data
        # ----------------------------------------------------

        permutation = (
            rng.permutation(
                num_samples
            )
        )


        X_shuffled = (
            X_train[
                permutation
            ]
        )


        Y_shuffled = (
            Y_train[
                permutation
            ]
        )


        epoch_loss = 0.0
        num_batches = 0


        # ----------------------------------------------------
        # Mini-batch training
        # ----------------------------------------------------

        for start in range(
            0,
            num_samples,
            batch_size
        ):

            end = min(
                start + batch_size,
                num_samples
            )


            X_batch = (
                X_shuffled[
                    start:end
                ]
            )


            Y_batch = (
                Y_shuffled[
                    start:end
                ]
            )


            # ------------------------------------------------
            # Forward propagation
            # ------------------------------------------------

            Y_pred, cache = (
                forward_pass(
                    X_batch,
                    W1,
                    b1,
                    W2,
                    b2,
                    W3,
                    b3,
                    activation1,
                    activation2
                )
            )


            # ------------------------------------------------
            # Loss
            # ------------------------------------------------

            loss = (
                cross_entropy_loss(
                    Y_batch,
                    Y_pred
                )
            )


            epoch_loss += loss

            num_batches += 1


            # ------------------------------------------------
            # Backpropagation
            # ------------------------------------------------

            gradients = (
                backward_pass(
                    Y_batch,
                    cache,
                    W2,
                    W3,
                    activation1,
                    activation2
                )
            )


            (
                dW1,
                db1,
                dW2,
                db2,
                dW3,
                db3
            ) = gradients


            # ------------------------------------------------
            # Gradient descent update
            # ------------------------------------------------

            W1 -= (
                learning_rate *
                dW1
            )

            b1 -= (
                learning_rate *
                db1
            )


            W2 -= (
                learning_rate *
                dW2
            )

            b2 -= (
                learning_rate *
                db2
            )


            W3 -= (
                learning_rate *
                dW3
            )

            b3 -= (
                learning_rate *
                db3
            )


        # ----------------------------------------------------
        # Average loss for epoch
        # ----------------------------------------------------

        epoch_loss /= (
            num_batches
        )


        loss_history.append(
            epoch_loss
        )


    # ========================================================
    # TRAINING TIME
    # ========================================================

    training_time = (
        time.perf_counter()
        - start_time
    )


    # --------------------------------------------------------
    # Store parameters
    # --------------------------------------------------------

    parameters = (
        W1,
        b1,
        W2,
        b2,
        W3,
        b3
    )


    return (
        parameters,
        loss_history,
        training_time
    )


# ============================================================
# 9. PREDICTION FUNCTION
# ============================================================

def predict_network(
    X,
    parameters,
    activation1,
    activation2
):

    (
        W1,
        b1,
        W2,
        b2,
        W3,
        b3
    ) = parameters


    probabilities, _ = (
        forward_pass(
            X,
            W1,
            b1,
            W2,
            b2,
            W3,
            b3,
            activation1,
            activation2
        )
    )


    predictions = np.argmax(
        probabilities,
        axis=1
    )


    return (
        predictions,
        probabilities
    )


# ============================================================
# 10. MACRO-F1
# ============================================================

def macro_f1_score(
    y_true,
    y_pred,
    num_classes
):

    f1_scores = []


    for cls in range(
        num_classes
    ):

        # ----------------------------------------------------
        # True Positives
        # ----------------------------------------------------

        true_positive = np.sum(
            (y_true == cls) &
            (y_pred == cls)
        )


        # ----------------------------------------------------
        # False Positives
        # ----------------------------------------------------

        false_positive = np.sum(
            (y_true != cls) &
            (y_pred == cls)
        )


        # ----------------------------------------------------
        # False Negatives
        # ----------------------------------------------------

        false_negative = np.sum(
            (y_true == cls) &
            (y_pred != cls)
        )


        # ----------------------------------------------------
        # Precision
        # ----------------------------------------------------

        if (
            true_positive +
            false_positive
        ) == 0:

            precision = 0.0

        else:

            precision = (
                true_positive /
                (
                    true_positive +
                    false_positive
                )
            )


        # ----------------------------------------------------
        # Recall
        # ----------------------------------------------------

        if (
            true_positive +
            false_negative
        ) == 0:

            recall = 0.0

        else:

            recall = (
                true_positive /
                (
                    true_positive +
                    false_negative
                )
            )


        # ----------------------------------------------------
        # F1
        # ----------------------------------------------------

        if (
            precision +
            recall
        ) == 0:

            f1 = 0.0

        else:

            f1 = (
                2 *
                precision *
                recall /
                (
                    precision +
                    recall
                )
            )


        f1_scores.append(
            f1
        )


    return np.mean(
        f1_scores
    )


# ============================================================
# 11. VERIFY PCA DATA
# ============================================================

print("=" * 60)
print("STEP 4 - PCA NEURAL NETWORK EXPERIMENT")
print("=" * 60)

print(
    "\nPCA input dimension:",
    n_components
)

print(
    "Training data shape:",
    X_train_pca.shape
)

print(
    "Testing data shape:",
    X_test_pca.shape
)


# ============================================================
# 12. COMMON TRAINING SETTINGS
# ============================================================

learning_rate = 0.01
batch_size = 32
epochs = 100
seed = 42


# ============================================================
# 13. CONFIGURATION A
# ReLU + ReLU + Softmax
# ============================================================

print(
    "\nTraining Configuration A..."
)

parameters_A, loss_A, time_A = (
    train_network(
        X_train_pca,
        Y_train,
        n_components,
        "relu",
        "relu",
        learning_rate,
        batch_size,
        epochs,
        seed
    )
)


pred_A, prob_A = (
    predict_network(
        X_test_pca,
        parameters_A,
        "relu",
        "relu"
    )
)


accuracy_A = np.mean(
    pred_A == y_test
)


f1_A = macro_f1_score(
    y_test,
    pred_A,
    7
)


print(
    "Configuration A complete."
)

print(
    f"Accuracy : {accuracy_A * 100:.2f}%"
)

print(
    f"Macro-F1 : {f1_A:.4f}"
)

print(
    f"Time     : {time_A:.4f} seconds"
)


# ============================================================
# 14. CONFIGURATION B
# ReLU + Sigmoid + Softmax
# ============================================================

print(
    "\nTraining Configuration B..."
)

parameters_B, loss_B, time_B = (
    train_network(
        X_train_pca,
        Y_train,
        n_components,
        "relu",
        "sigmoid",
        learning_rate,
        batch_size,
        epochs,
        seed
    )
)


pred_B, prob_B = (
    predict_network(
        X_test_pca,
        parameters_B,
        "relu",
        "sigmoid"
    )
)


accuracy_B = np.mean(
    pred_B == y_test
)


f1_B = macro_f1_score(
    y_test,
    pred_B,
    7
)


print(
    "Configuration B complete."
)

print(
    f"Accuracy : {accuracy_B * 100:.2f}%"
)

print(
    f"Macro-F1 : {f1_B:.4f}"
)

print(
    f"Time     : {time_B:.4f} seconds"
)


# ============================================================
# 15. CONFIGURATION C
# Sigmoid + ReLU + Softmax
# ============================================================

print(
    "\nTraining Configuration C..."
)

parameters_C, loss_C, time_C = (
    train_network(
        X_train_pca,
        Y_train,
        n_components,
        "sigmoid",
        "relu",
        learning_rate,
        batch_size,
        epochs,
        seed
    )
)


pred_C, prob_C = (
    predict_network(
        X_test_pca,
        parameters_C,
        "sigmoid",
        "relu"
    )
)


accuracy_C = np.mean(
    pred_C == y_test
)


f1_C = macro_f1_score(
    y_test,
    pred_C,
    7
)


print(
    "Configuration C complete."
)

print(
    f"Accuracy : {accuracy_C * 100:.2f}%"
)

print(
    f"Macro-F1 : {f1_C:.4f}"
)

print(
    f"Time     : {time_C:.4f} seconds"
)


# ============================================================
# 16. CONFIGURATION D
# Sigmoid + Sigmoid + Softmax
# ============================================================

print(
    "\nTraining Configuration D..."
)

parameters_D, loss_D, time_D = (
    train_network(
        X_train_pca,
        Y_train,
        n_components,
        "sigmoid",
        "sigmoid",
        learning_rate,
        batch_size,
        epochs,
        seed
    )
)


pred_D, prob_D = (
    predict_network(
        X_test_pca,
        parameters_D,
        "sigmoid",
        "sigmoid"
    )
)


accuracy_D = np.mean(
    pred_D == y_test
)


f1_D = macro_f1_score(
    y_test,
    pred_D,
    7
)


print(
    "Configuration D complete."
)

print(
    f"Accuracy : {accuracy_D * 100:.2f}%"
)

print(
    f"Macro-F1 : {f1_D:.4f}"
)

print(
    f"Time     : {time_D:.4f} seconds"
)


# ============================================================
# 17. CONFIGURATION E
# Mixed:
# Layer 1: 8 ReLU + 8 Sigmoid
# Layer 2: 4 ReLU + 4 Sigmoid
# ============================================================

print(
    "\nTraining Configuration E..."
)

parameters_E, loss_E, time_E = (
    train_network(
        X_train_pca,
        Y_train,
        n_components,
        "mixed",
        "mixed",
        learning_rate,
        batch_size,
        epochs,
        seed
    )
)


pred_E, prob_E = (
    predict_network(
        X_test_pca,
        parameters_E,
        "mixed",
        "mixed"
    )
)


accuracy_E = np.mean(
    pred_E == y_test
)


f1_E = macro_f1_score(
    y_test,
    pred_E,
    7
)


print(
    "Configuration E complete."
)

print(
    f"Accuracy : {accuracy_E * 100:.2f}%"
)

print(
    f"Macro-F1 : {f1_E:.4f}"
)

print(
    f"Time     : {time_E:.4f} seconds"
)


# ============================================================
# 18. INDIVIDUAL LOSS CURVES
# ============================================================

plt.figure(
    figsize=(9, 5)
)

plt.plot(
    range(1, epochs + 1),
    loss_A
)

plt.xlabel(
    "Epoch"
)

plt.ylabel(
    "Training Loss"
)

plt.title(
    "Configuration A - ReLU + ReLU"
)

plt.grid(True)

plt.show()


plt.figure(
    figsize=(9, 5)
)

plt.plot(
    range(1, epochs + 1),
    loss_B
)

plt.xlabel(
    "Epoch"
)

plt.ylabel(
    "Training Loss"
)

plt.title(
    "Configuration B - ReLU + Sigmoid"
)

plt.grid(True)

plt.show()


plt.figure(
    figsize=(9, 5)
)

plt.plot(
    range(1, epochs + 1),
    loss_C
)

plt.xlabel(
    "Epoch"
)

plt.ylabel(
    "Training Loss"
)

plt.title(
    "Configuration C - Sigmoid + ReLU"
)

plt.grid(True)

plt.show()


plt.figure(
    figsize=(9, 5)
)

plt.plot(
    range(1, epochs + 1),
    loss_D
)

plt.xlabel(
    "Epoch"
)

plt.ylabel(
    "Training Loss"
)

plt.title(
    "Configuration D - Sigmoid + Sigmoid"
)

plt.grid(True)

plt.show()


plt.figure(
    figsize=(9, 5)
)

plt.plot(
    range(1, epochs + 1),
    loss_E
)

plt.xlabel(
    "Epoch"
)

plt.ylabel(
    "Training Loss"
)

plt.title(
    "Configuration E - Mixed"
)

plt.grid(True)

plt.show()


# ============================================================
# 19. COMBINED LOSS CURVE
# ============================================================

plt.figure(
    figsize=(10, 6)
)

plt.plot(
    loss_A,
    label="A: ReLU + ReLU"
)

plt.plot(
    loss_B,
    label="B: ReLU + Sigmoid"
)

plt.plot(
    loss_C,
    label="C: Sigmoid + ReLU"
)

plt.plot(
    loss_D,
    label="D: Sigmoid + Sigmoid"
)

plt.plot(
    loss_E,
    label="E: Mixed"
)

plt.xlabel(
    "Epoch"
)

plt.ylabel(
    "Training Loss"
)

plt.title(
    "Training Loss Comparison"
)

plt.legend()

plt.grid(True)

plt.show()


# ============================================================
# 20. RESULT TABLE
# ============================================================

results = pd.DataFrame({

    "Configuration": [
        "A: ReLU + ReLU",
        "B: ReLU + Sigmoid",
        "C: Sigmoid + ReLU",
        "D: Sigmoid + Sigmoid",
        "E: Mixed"
    ],

    "Input Dimension": [
        n_components,
        n_components,
        n_components,
        n_components,
        n_components
    ],

    "Accuracy": [
        accuracy_A,
        accuracy_B,
        accuracy_C,
        accuracy_D,
        accuracy_E
    ],

    "Macro-F1": [
        f1_A,
        f1_B,
        f1_C,
        f1_D,
        f1_E
    ],

    "Training Time (s)": [
        time_A,
        time_B,
        time_C,
        time_D,
        time_E
    ]
})


# ============================================================
# 21. FORMAT RESULT TABLE
# ============================================================

results_display = results.copy()


results_display["Accuracy"] = (
    results_display["Accuracy"] * 100
)


results_display["Accuracy"] = (
    results_display["Accuracy"].round(2)
)


results_display["Macro-F1"] = (
    results_display["Macro-F1"].round(4)
)


results_display["Training Time (s)"] = (
    results_display["Training Time (s)"].round(4)
)


print("\n")
print("=" * 70)
print("STEP 4 RESULT TABLE")
print("=" * 70)

print(
    results_display.to_string(
        index=False
    )
)

print("=" * 70)


# ============================================================
# 22. DETERMINE BEST CONFIGURATION
# ============================================================

best_index = (
    results["Macro-F1"].idxmax()
)

best_configuration = (
    results.loc[
        best_index,
        "Configuration"
    ]
)

best_f1 = (
    results.loc[
        best_index,
        "Macro-F1"
    ]
)

best_accuracy = (
    results.loc[
        best_index,
        "Accuracy"
    ]
)

best_time = (
    results.loc[
        best_index,
        "Training Time (s)"
    ]
)


print(
    "\nBest configuration based on Macro-F1:"
)

print(
    best_configuration
)

print(
    f"Accuracy : "
    f"{best_accuracy * 100:.2f}%"
)

print(
    f"Macro-F1 : "
    f"{best_f1:.4f}"
)

print(
    f"Time     : "
    f"{best_time:.4f} seconds"
)

# ============================================================
# STEP 5
# MODEL COMPARISON + CONFUSION MATRICES + INTERFACE
# ============================================================

from matplotlib.widgets import TextBox, Button


# ============================================================
# 1. COUNT TRAINABLE PARAMETERS
# ============================================================

def count_parameters(
    input_dim,
    hidden1=16,
    hidden2=8,
    output_dim=7
):

    layer1 = (
        input_dim * hidden1 +
        hidden1
    )

    layer2 = (
        hidden1 * hidden2 +
        hidden2
    )

    layer3 = (
        hidden2 * output_dim +
        output_dim
    )

    return (
        layer1 +
        layer2 +
        layer3
    )


original_parameters = (
    count_parameters(27)
)

pca_parameters = (
    count_parameters(n_components)
)


print(
    "Original model parameters:",
    original_parameters
)

print(
    "PCA model parameters:",
    pca_parameters
)


# ============================================================
# 2. SELECT BEST PCA MODEL
# ============================================================

best_index = (
    results["Macro-F1"].idxmax()
)

best_configuration = (
    results.loc[
        best_index,
        "Configuration"
    ]
)


if best_index == 0:

    best_parameters = parameters_A
    best_loss = loss_A
    best_time = time_A
    best_predictions = pred_A
    best_probabilities = prob_A
    best_activation1 = "relu"
    best_activation2 = "relu"


elif best_index == 1:

    best_parameters = parameters_B
    best_loss = loss_B
    best_time = time_B
    best_predictions = pred_B
    best_probabilities = prob_B
    best_activation1 = "relu"
    best_activation2 = "sigmoid"


elif best_index == 2:

    best_parameters = parameters_C
    best_loss = loss_C
    best_time = time_C
    best_predictions = pred_C
    best_probabilities = prob_C
    best_activation1 = "sigmoid"
    best_activation2 = "relu"


elif best_index == 3:

    best_parameters = parameters_D
    best_loss = loss_D
    best_time = time_D
    best_predictions = pred_D
    best_probabilities = prob_D
    best_activation1 = "sigmoid"
    best_activation2 = "sigmoid"


else:

    best_parameters = parameters_E
    best_loss = loss_E
    best_time = time_E
    best_predictions = pred_E
    best_probabilities = prob_E
    best_activation1 = "mixed"
    best_activation2 = "mixed"


# ============================================================
# 3. BEST PCA METRICS
# ============================================================

best_accuracy = np.mean(
    best_predictions == y_test
)

best_macro_f1 = macro_f1_score(
    y_test,
    best_predictions,
    7
)


# ============================================================
# 4. MODEL COMPARISON TABLE
# ============================================================

comparison = pd.DataFrame({

    "Model": [
        "Original Features",
        "Best PCA Model"
    ],

    "Input Dimensions": [
        27,
        n_components
    ],

    "Trainable Parameters": [
        original_parameters,
        pca_parameters
    ],

    "Accuracy (%)": [
        test_accuracy * 100,
        best_accuracy * 100
    ],

    "Macro-F1": [
        test_macro_f1,
        best_macro_f1
    ],

    "Training Time (s)": [
        training_time,
        best_time
    ]
})


comparison["Accuracy (%)"] = (
    comparison["Accuracy (%)"].round(2)
)

comparison["Macro-F1"] = (
    comparison["Macro-F1"].round(4)
)

comparison["Training Time (s)"] = (
    comparison["Training Time (s)"].round(4)
)


print("\n")
print("=" * 75)
print("MODEL COMPARISON")
print("=" * 75)

print(
    comparison.to_string(
        index=False
    )
)

print("=" * 75)


# ============================================================
# 5. CONFUSION MATRIX
# ============================================================

def confusion_matrix(
    y_true,
    y_pred,
    num_classes
):

    cm = np.zeros(
        (
            num_classes,
            num_classes
        ),
        dtype=int
    )

    for actual, predicted in zip(
        y_true,
        y_pred
    ):

        cm[
            actual,
            predicted
        ] += 1

    return cm


cm_original = confusion_matrix(
    y_test,
    test_predictions,
    7
)

cm_pca = confusion_matrix(
    y_test,
    best_predictions,
    7
)


# ============================================================
# 6. PLOT CONFUSION MATRIX
# ============================================================

def plot_confusion_matrix(
    cm,
    class_names,
    title
):

    plt.figure(
        figsize=(9, 7)
    )

    plt.imshow(
        cm,
        cmap="Blues"
    )

    plt.colorbar(
        label="Number of Samples"
    )

    plt.xticks(
        np.arange(
            len(class_names)
        ),
        class_names,
        rotation=45,
        ha="right"
    )

    plt.yticks(
        np.arange(
            len(class_names)
        ),
        class_names
    )

    plt.xlabel(
        "Predicted Class"
    )

    plt.ylabel(
        "Actual Class"
    )

    plt.title(
        title
    )


    for i in range(
        cm.shape[0]
    ):

        for j in range(
            cm.shape[1]
        ):

            plt.text(
                j,
                i,
                cm[i, j],
                ha="center",
                va="center"
            )


    plt.tight_layout()

    plt.show()


plot_confusion_matrix(
    cm_original,
    class_names,
    "Confusion Matrix - Original Feature Model"
)


plot_confusion_matrix(
    cm_pca,
    class_names,
    "Confusion Matrix - Best PCA Model"
)


# ============================================================
# 7. ORIGINAL INPUT -> MODEL PREDICTION
# ============================================================

def predict_original_input(
    raw_features,
    model_type="pca"
):

    X_input = np.asarray(
        raw_features,
        dtype=float
    ).reshape(
        1,
        -1
    )


    if X_input.shape[1] != 27:

        raise ValueError(
            "Expected exactly 27 features."
        )


    # --------------------------------------------------------
    # Standardization
    # --------------------------------------------------------

    X_input_std = (
        X_input -
        mean_train
    ) / std_train


    # --------------------------------------------------------
    # PCA model
    # --------------------------------------------------------

    if model_type == "pca":

        X_input_pca = (
            X_input_std @
            principal_components
        )


        probabilities, _ = (
            forward_pass(
                X_input_pca,
                *best_parameters,
                best_activation1,
                best_activation2
            )
        )


    # --------------------------------------------------------
    # Original model
    # --------------------------------------------------------

    elif model_type == "original":

        probabilities, _ = (
            forward_pass(
                X_input,
                W1,
                b1,
                W2,
                b2,
                W3,
                b3,
                "relu",
                "relu"
            )
        )


    else:

        raise ValueError(
            "Unknown model type."
        )


    predicted_class = np.argmax(
        probabilities[0]
    )

    confidence = np.max(
        probabilities[0]
    )


    return (
        predicted_class,
        confidence,
        probabilities[0]
    )


# ============================================================
# 8. INTERACTIVE MATPLOTLIB INTERFACE
# ============================================================
def launch_interface():

    fig = plt.figure(
        figsize=(14, 12)
    )

    fig.suptitle(
        "Steel Plate Fault Classifier",
        fontsize=16
    )

    # ========================================================
    # Create 27 input axes
    # ========================================================

    input_axes = []

    for i in range(27):

        column = i // 14
        row = i % 14

        if column == 0:
            x = 0.17
        else:
            x = 0.61

        y = 0.90 - row * 0.055

        # Label
        label_ax = fig.add_axes([
            x - 0.08,
            y,
            0.07,
            0.035
        ])

        label_ax.axis("off")

        label_ax.text(
            1.0,
            0.5,
            f"Feature {i + 1}",
            ha="right",
            va="center"
        )

        # Input box
        input_ax = fig.add_axes([
            x,
            y,
            0.13,
            0.035
        ])

        input_ax.set_xticks([])
        input_ax.set_yticks([])

        input_ax.set_facecolor("white")

        for spine in input_ax.spines.values():
            spine.set_visible(True)

        input_axes.append(input_ax)


    # ========================================================
    # Store typed values
    # ========================================================

    values = [
        ""
        for _ in range(27)
    ]

    active_box = [
        None
    ]


    # ========================================================
    # Display text inside boxes
    # ========================================================

    text_objects = []

    for ax in input_axes:

        text = ax.text(
            0.03,
            0.5,
            "",
            transform=ax.transAxes,
            ha="left",
            va="center",
            fontsize=10
        )

        text_objects.append(text)


    # ========================================================
    # Mouse click
    # ========================================================

    def mouse_click(event):

        if event.inaxes in input_axes:

            index = input_axes.index(
                event.inaxes
            )

            active_box[0] = index

            fig.canvas.draw_idle()


    fig.canvas.mpl_connect(
        "button_press_event",
        mouse_click
    )


    # ========================================================
    # Keyboard input
    # ========================================================

    def keyboard_input(event):

        index = active_box[0]

        if index is None:
            return


        # ----------------------------------------------------
        # Normal characters
        # ----------------------------------------------------

        if event.key in (
            "0", "1", "2", "3", "4",
            "5", "6", "7", "8", "9",
            ".", "-", "e", "E", "+"
        ):

            values[index] += event.key


        # ----------------------------------------------------
        # Backspace
        # ----------------------------------------------------

        elif event.key == "backspace":

            values[index] = (
                values[index][:-1]
            )


        # ----------------------------------------------------
        # Delete entire value
        # ----------------------------------------------------

        elif event.key == "delete":

            values[index] = ""


        # ----------------------------------------------------
        # Move to next box
        # ----------------------------------------------------

        elif event.key in (
            "enter",
            "tab"
        ):

            if index < 26:

                active_box[0] = index + 1


        # ----------------------------------------------------
        # Move to previous box
        # ----------------------------------------------------

        elif event.key == "shift+tab":

            if index > 0:

                active_box[0] = index - 1


        else:

            return


        # ----------------------------------------------------
        # Update displayed value
        # ----------------------------------------------------

        text_objects[index].set_text(
            values[index]
        )

        fig.canvas.draw_idle()


    fig.canvas.mpl_connect(
        "key_press_event",
        keyboard_input
    )


    # ========================================================
    # Predict button
    # ========================================================

    button_ax = fig.add_axes([
        0.38,
        0.08,
        0.24,
        0.06
    ])


    predict_button = Button(
        button_ax,
        "Predict"
    )


    # ========================================================
    # Result area
    # ========================================================

    result_ax = fig.add_axes([
        0.20,
        0.01,
        0.60,
        0.05
    ])

    result_ax.axis("off")


    result_text = result_ax.text(
        0.5,
        0.5,
        "Enter all 27 features.",
        ha="center",
        va="center",
        fontsize=12
    )


    # ========================================================
    # Prediction callback
    # ========================================================

    def predict_callback(event):

        try:

            # -----------------------------------------------
            # Check that all fields contain values
            # -----------------------------------------------

            if any(
                value.strip() == ""
                for value in values
            ):

                result_text.set_text(
                    "Please enter all 27 features."
                )

                fig.canvas.draw_idle()

                return


            # -----------------------------------------------
            # Convert to numbers
            # -----------------------------------------------

            numerical_values = [
                float(value)
                for value in values
            ]


            # -----------------------------------------------
            # Predict
            # -----------------------------------------------

            predicted_class, confidence, probabilities = (
                predict_original_input(
                    numerical_values,
                    model_type="pca"
                )
            )


            predicted_name = (
                class_names[
                    predicted_class
                ]
            )


            # -----------------------------------------------
            # Display result
            # -----------------------------------------------

            result_text.set_text(
                f"Predicted Fault: "
                f"{predicted_name}    |    "
                f"Confidence: "
                f"{confidence * 100:.2f}%"
            )


            fig.canvas.draw_idle()


        except ValueError:

            result_text.set_text(
                "Please enter valid numeric values."
            )

            fig.canvas.draw_idle()


    predict_button.on_clicked(
        predict_callback
    )


    # ========================================================
    # Show interface
    # ========================================================

    plt.show()


# ============================================================
# 9. TEST INTERFACE ON THREE TEST RECORDS
# ============================================================

interface_test_results = []


for i in range(3):

    interface_prediction, confidence, probabilities = (
        predict_original_input(
            X_test[i],
            model_type="pca"
        )
    )


    interface_test_results.append({

        "Record": i + 1,

        "Actual Fault":
            class_names[
                y_test[i]
            ],

        "Predicted Fault":
            class_names[
                interface_prediction
            ],

        "Confidence (%)":
            confidence * 100,

        "Model Prediction":
            class_names[
                best_predictions[i]
            ],

        "Match":
            interface_prediction ==
            best_predictions[i]
    })


interface_test_results = pd.DataFrame(
    interface_test_results
)


interface_test_results[
    "Confidence (%)"
] = interface_test_results[
    "Confidence (%)"
].round(2)


print("\n")
print("=" * 75)
print("INTERFACE VERIFICATION")
print("=" * 75)

print(
    interface_test_results.to_string(
        index=False
    )
)

print("=" * 75)


# ============================================================
# 10. LAUNCH INTERFACE
# ============================================================

launch_interface()
