import numpy as np
import matplotlib.pyplot as plt

from exp1 import prepare_data
from model import SingleNeuron

RANDOM_SEED = 42
MAX_EPOCHS = 100
LEARNING_RATE = 0.01


def main():
    np.random.seed(RANDOM_SEED)

    X_train, X_test, y_train, y_test, x_scaler, y_scaler = prepare_data()

    neuron = SingleNeuron(w1_init=1.5, w2_init=-1.5)
    loss_history = []

    for _ in range(MAX_EPOCHS):
        y_pred = neuron.forward(X_train)
        loss = neuron.mse_loss(y_train, y_pred)
        loss_history.append(loss)

        grad = neuron.gradients(X_train, y_train, y_pred)
        neuron.w -= LEARNING_RATE * grad

    y_train_pred = neuron.forward(X_train)
    y_test_pred = neuron.forward(X_test)
    train_mse = neuron.mse_loss(y_train, y_train_pred)
    test_mse = neuron.mse_loss(y_test, y_test_pred)

    print(f"Initial weights : w1=1.5000, w2=-1.5000")
    print(f"Final weights   : w1={neuron.w[0]:.4f}, w2={neuron.w[1]:.4f}")
    print(f"Initial loss    : {loss_history[0]:.4f}")
    print(f"Final train MSE : {train_mse:.4f}")
    print(f"Final test MSE  : {test_mse:.4f}")

    plt.figure(figsize=(6, 4))
    plt.plot(range(1, MAX_EPOCHS + 1), loss_history)
    plt.xlabel("Epoch")
    plt.ylabel("MSE Loss (standardized scale)")
    plt.title("Task 2: Single-Neuron Training Loss (Batch GD, lr=0.01)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("task2_loss_curve.png", dpi=150)
    print("\nSaved loss curve to task2_loss_curve.png")


if __name__ == "__main__":
    main()
