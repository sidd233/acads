import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# -----------------------------
# Load dataset
# -----------------------------
df = pd.read_csv("and.csv")
print(df)

# -----------------------------
# Initial perceptron parameters
# -----------------------------
w1 = 1.0
w2 = 1.0
w3 = 1.0
b = -2.5

# -----------------------------
# Create figure
# -----------------------------
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

plt.subplots_adjust(bottom=0.35)

# -----------------------------
# Scatter plot
# -----------------------------
scatter = ax.scatter(
    df["A"],
    df["B"],
    df["C"],
    c=df["Output"],
    cmap="viridis",
    s=100
)

ax.set_xlabel("Input A")
ax.set_ylabel("Input B")
ax.set_zlabel("Input C")
ax.set_title("Interactive Perceptron Decision Hyperplane")

plt.colorbar(scatter, label="Output")

# -----------------------------
# Mesh grid for plane
# -----------------------------
x = np.linspace(0, 1, 10)
y = np.linspace(0, 1, 10)
X, Y = np.meshgrid(x, y)

plane = None

# -----------------------------
# Function to draw plane
# -----------------------------
def draw_plane(w1, w2, w3, b):
    global plane

    if plane is not None:
        plane.remove()

    if abs(w3) < 1e-6:
        fig.canvas.draw_idle()
        return

    Z = -(w1 * X + w2 * Y + b) / w3

    plane = ax.plot_surface(
        X,
        Y,
        Z,
        alpha=0.4,
        color="red"
    )

    fig.canvas.draw_idle()

draw_plane(w1, w2, w3, b)

# -----------------------------
# Slider Axes
# -----------------------------
ax_w1 = plt.axes([0.20, 0.25, 0.65, 0.03])
ax_w2 = plt.axes([0.20, 0.20, 0.65, 0.03])
ax_w3 = plt.axes([0.20, 0.15, 0.65, 0.03])
ax_b = plt.axes([0.20, 0.10, 0.65, 0.03])

# -----------------------------
# Sliders
# -----------------------------
slider_w1 = Slider(ax_w1, "Weight 1", -5, 5, valinit=w1)
slider_w2 = Slider(ax_w2, "Weight 2", -5, 5, valinit=w2)
slider_w3 = Slider(ax_w3, "Weight 3", -5, 5, valinit=w3)
slider_b = Slider(ax_b, "Bias", -5, 5, valinit=b)

# -----------------------------
# Update function
# -----------------------------
def update(val):
    draw_plane(
        slider_w1.val,
        slider_w2.val,
        slider_w3.val,
        slider_b.val
    )

slider_w1.on_changed(update)
slider_w2.on_changed(update)
slider_w3.on_changed(update)
slider_b.on_changed(update)

plt.show()