import gzip
import struct
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

ROOT = Path(__file__).parent
RAW = ROOT / "data" / "MNIST" / "raw"
CKPT = ROOT / "lenet_mnist.pt"
SEED = 42
MEAN, STD = 0.1307, 0.3081
N_TEST = 2000  # size of the test set scanned in Experiments 2-6 (seeded subset of MNIST test)


class LeNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 6, 5)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.pool = nn.AvgPool2d(2)
        self.fc1 = nn.Linear(256, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        x = self.pool(torch.relu(self.conv1(x)))
        x = self.pool(torch.relu(self.conv2(x)))
        x = x.flatten(1)
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)

    def feature_maps(self, x):
        """Returns PRE-ReLU maps (Z1, Z2) of Conv1 and Conv2."""
        z1 = self.conv1(x)
        z2 = self.conv2(self.pool(torch.relu(z1)))
        return z1, z2


def _read_idx(name):
    p = RAW / name
    with (gzip.open(str(p) + ".gz") if not p.exists() else open(p, "rb")) as f:
        data = f.read()
    ndim = data[3]
    shape = struct.unpack(">" + "I" * ndim, data[4:4 + 4 * ndim])
    return np.frombuffer(data, np.uint8, offset=4 + 4 * ndim).reshape(shape)


def load_mnist(split):
    prefix = "train" if split == "train" else "t10k"
    x = _read_idx(f"{prefix}-images-idx3-ubyte")
    y = _read_idx(f"{prefix}-labels-idx1-ubyte")
    return x, y


def to_tensor(x_uint8):
    x = torch.from_numpy(x_uint8.astype(np.float32) / 255.0).unsqueeze(1)
    return (x - MEAN) / STD
