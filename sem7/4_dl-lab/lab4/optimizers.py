"""
Task 3: Nine optimizers implemented from scratch and applied to the
single-neuron model from Task 2 (model.py).
"""

import numpy as np

from model import SingleNeuron

RANDOM_SEED = 42
MAX_EPOCHS = 100
LEARNING_RATE = 0.01
GAMMA = 0.9          # momentum / Nesterov coefficient
EPS = 1e-8           # AdaGrad / RMSProp epsilon
BETA = 0.9           # RMSProp decay
W_INIT = (1.5, -1.5)

class PlainOptimizer:
    """w_{t+1} = w_t - eta * g_t  (used for BGD, Mini-Batch GD, SGD)."""

    def __init__(self, lr):
        self.lr = lr

    def eval_point(self, w):
        return w

    def step(self, w, grad):
        return w - self.lr * grad


class MomentumOptimizer:
    """update_t = gamma*update_{t-1} + eta*grad, w_{t+1} = w_t - update_t.
    Used for Momentum GD and SGD with Momentum."""

    def __init__(self, lr, gamma=GAMMA):
        self.lr = lr
        self.gamma = gamma
        self.v = np.zeros(2)

    def eval_point(self, w):
        return w

    def step(self, w, grad):
        self.v = self.gamma * self.v + self.lr * grad
        return w - self.v


class NesterovOptimizer:
    """w_look = w_t - gamma*v_{t-1}, v_t = gamma*v_{t-1} + eta*grad(w_look),
    w_{t+1} = w_t - v_t. Used for NAG and Nesterov SGD."""

    def __init__(self, lr, gamma=GAMMA):
        self.lr = lr
        self.gamma = gamma
        self.v = np.zeros(2)

    def eval_point(self, w):
        return w - self.gamma * self.v

    def step(self, w, grad):
        self.v = self.gamma * self.v + self.lr * grad
        return w - self.v


class AdaGradOptimizer:
    """v_t = v_{t-1} + grad^2, w_{t+1} = w_t - eta/sqrt(v_t+eps) * grad."""

    def __init__(self, lr, eps=EPS):
        self.lr = lr
        self.eps = eps
        self.v = np.zeros(2)

    def eval_point(self, w):
        return w

    def step(self, w, grad):
        self.v = self.v + grad ** 2
        return w - (self.lr / np.sqrt(self.v + self.eps)) * grad


class RMSPropOptimizer:
    """v_t = beta*v_{t-1} + (1-beta)*grad^2, w_{t+1} = w_t - eta/sqrt(v_t+eps)*grad."""

    def __init__(self, lr, beta=BETA, eps=EPS):
        self.lr = lr
        self.beta = beta
        self.eps = eps
        self.v = np.zeros(2)

    def eval_point(self, w):
        return w

    def step(self, w, grad):
        self.v = self.beta * self.v + (1 - self.beta) * grad ** 2
        return w - (self.lr / np.sqrt(self.v + self.eps)) * grad


# ---------------------------------------------------------------------------
# Generic training loop shared by all nine optimizers.
# ---------------------------------------------------------------------------

def train(X, y, optimizer, batch_size, max_epochs=MAX_EPOCHS,
          seed=RANDOM_SEED, shuffle=False, w_init=W_INIT):
    """Runs `optimizer` over (X, y) for `max_epochs` full passes.

    Returns a dict with:
      w_final        : final [w1, w2]
      weight_history : (n_updates+1, 2) array, weights after every update
                        (index 0 is the initial weights)
      epoch_loss      : (max_epochs,) full-training-set MSE at the end of
                        each epoch (used for convergence comparisons)
      n_updates       : total number of parameter updates performed
    """
    n = X.shape[0]
    rng = np.random.RandomState(seed)

    w = np.array(w_init, dtype=float)
    weight_history = [w.copy()]
    epoch_loss = []
    n_updates = 0

    for epoch in range(max_epochs):
        order = rng.permutation(n) if shuffle else np.arange(n)

        for start in range(0, n, batch_size):
            batch_idx = order[start:start + batch_size]
            Xb, yb = X[batch_idx], y[batch_idx]

            w_eval = optimizer.eval_point(w)
            y_pred = Xb @ w_eval
            grad = (2.0 / len(batch_idx)) * (Xb.T @ (y_pred - yb))

            w = optimizer.step(w, grad)
            n_updates += 1
            weight_history.append(w.copy())

        full_pred = X @ w
        epoch_loss.append(np.mean((y - full_pred) ** 2))

    return {
        "w_final": w,
        "weight_history": np.array(weight_history),
        "epoch_loss": np.array(epoch_loss),
        "n_updates": n_updates,
    }


# ---------------------------------------------------------------------------
# The nine optimizer configurations required by Task 3.
# ---------------------------------------------------------------------------

def build_optimizer_configs(n_train):
    return {
        "BGD": dict(optimizer=PlainOptimizer(LEARNING_RATE),
                    batch_size=n_train, shuffle=False),
        "MBGD": dict(optimizer=PlainOptimizer(LEARNING_RATE),
                     batch_size=16, shuffle=True),
        "Momentum GD": dict(optimizer=MomentumOptimizer(LEARNING_RATE, GAMMA),
                             batch_size=n_train, shuffle=False),
        "SGD": dict(optimizer=PlainOptimizer(LEARNING_RATE),
                    batch_size=1, shuffle=True),
        "SGD with Momentum": dict(optimizer=MomentumOptimizer(LEARNING_RATE, GAMMA),
                                   batch_size=1, shuffle=True),
        "NAG": dict(optimizer=NesterovOptimizer(LEARNING_RATE, GAMMA),
                    batch_size=n_train, shuffle=False),
        "Nesterov SGD": dict(optimizer=NesterovOptimizer(LEARNING_RATE, GAMMA),
                              batch_size=1, shuffle=True),
        "AdaGrad": dict(optimizer=AdaGradOptimizer(LEARNING_RATE, EPS),
                         batch_size=16, shuffle=True),
        "RMSProp": dict(optimizer=RMSPropOptimizer(LEARNING_RATE, BETA, EPS),
                         batch_size=16, shuffle=True),
    }


def run_all_optimizers(X_train, y_train):
    """Trains all nine optimizers once and returns {name: result_dict}."""
    configs = build_optimizer_configs(n_train=X_train.shape[0])
    results = {}
    for name, cfg in configs.items():
        results[name] = train(
            X_train, y_train,
            optimizer=cfg["optimizer"],
            batch_size=cfg["batch_size"],
            shuffle=cfg["shuffle"],
        )
    return results
