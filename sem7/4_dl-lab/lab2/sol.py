import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons
from matplotlib.patches import Circle

DEFAULT_INPUT = np.array([0.20, 0.80, 0.40])

DEFAULT_W1 = np.array([
    [1.60, -0.20,  0.20],
    [-1.20, 1.80, -0.30],
    [0.30, -0.20,  1.50]
])

DEFAULT_B1 = np.array([0.20, 0.10, -0.10])

DEFAULT_W2 = np.array([
    [-1.50,  1.60],
    [ 1.80, -1.20],
    [-1.30,  1.50]
])

DEFAULT_B2 = np.array([0.30, -0.20])

def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def tanh(x):
    return np.tanh(x)


def relu(x):
    return np.maximum(0, x)


def activation(x, name):
    if name == "Sigmoid":
        return sigmoid(x)
    elif name == "Tanh":
        return tanh(x)
    else:
        return relu(x)

def forward_propagation(x, W1, b1, W2, b2, activation_name):
    z1 = np.dot(x, W1) + b1
    a1 = activation(z1, activation_name)
    z2 = np.dot(a1, W2) + b2
    a2 = activation(z2, activation_name)

    return z1, a1, z2, a2


fig = plt.figure(figsize=(16, 10))
fig.canvas.manager.set_window_title(
    "Underground Mine Hazard Assessment"
)

network_ax = fig.add_axes([0.03, 0.28, 0.58, 0.68])
network_ax.set_xlim(0, 10)
network_ax.set_ylim(0, 10)
network_ax.axis("off")

input_positions = [
    (1.5, 8),
    (1.5, 5),
    (1.5, 2)
]

hidden_positions = [
    (5, 8),
    (5, 5),
    (5, 2)
]

output_positions = [
    (8.5, 6.5),
    (8.5, 3.5)
]

input_slider_axes = [
    fig.add_axes([0.08, 0.20, 0.35, 0.025]),
    fig.add_axes([0.08, 0.16, 0.35, 0.025]),
    fig.add_axes([0.08, 0.12, 0.35, 0.025])
]

input_names = [
    "Methane",
    "Oxygen",
    "Temperature"
]

input_sliders = []

for i in range(3):

    slider = Slider(
        input_slider_axes[i],
        input_names[i],
        0.00,
        1.00,
        valinit=DEFAULT_INPUT[i],
        valstep=0.01
    )

    input_sliders.append(slider)

weight_sliders = []

for i in range(3):
    for j in range(3):

        index = i * 3 + j

        y = 0.91 - index * 0.045

        ax = fig.add_axes([
            0.69,
            y,
            0.10,
            0.018
        ])

        slider = Slider(
            ax,
            f"W1[{i+1},{j+1}]",
            -2.0,
            2.0,
            valinit=DEFAULT_W1[i, j],
            valstep=0.1
        )

        weight_sliders.append(slider)

for i in range(3):
    for j in range(2):

        index = i * 2 + j

        y = 0.91 - index * 0.045

        ax = fig.add_axes([
            0.87,
            y,
            0.10,
            0.018
        ])

        slider = Slider(
            ax,
            f"W2[{i+1},{j+1}]",
            -2.0,
            2.0,
            valinit=DEFAULT_W2[i, j],
            valstep=0.1
        )

        weight_sliders.append(slider)

bias_sliders = []

default_biases = np.concatenate(
    [DEFAULT_B1, DEFAULT_B2]
)

bias_names = [
    "b1[1]",
    "b1[2]",
    "b1[3]",
    "b2[1]",
    "b2[2]"
]

for i in range(5):

    y = 0.42 - i * 0.045

    ax = fig.add_axes([
        0.69,
        y,
        0.12,
        0.018
    ])

    slider = Slider(
        ax,
        bias_names[i],
        -1.0,
        1.0,
        valinit=default_biases[i],
        valstep=0.1
    )

    bias_sliders.append(slider)

radio_ax = fig.add_axes([
    0.86,
    0.28,
    0.10,
    0.13
])

radio = RadioButtons(
    radio_ax,
    ["Sigmoid", "Tanh", "ReLU"],
    active=0
)

radio_ax.set_title("Activation")

reset_ax = fig.add_axes([
    0.70,
    0.12,
    0.10,
    0.05
])

random_ax = fig.add_axes([
    0.84,
    0.12,
    0.12,
    0.05
])

reset_button = Button(
    reset_ax,
    "Reset"
)

random_button = Button(
    random_ax,
    "Random Input"
)

def get_values():

    x = np.array([
        slider.val
        for slider in input_sliders
    ])

    W1 = np.array([
        slider.val
        for slider in weight_sliders[:9]
    ]).reshape(3, 3)

    W2 = np.array([
        slider.val
        for slider in weight_sliders[9:]
    ]).reshape(3, 2)

    b1 = np.array([
        slider.val
        for slider in bias_sliders[:3]
    ])

    b2 = np.array([
        slider.val
        for slider in bias_sliders[3:]
    ])

    activation_name = radio.value_selected

    return x, W1, b1, W2, b2, activation_name

def draw_connection(ax, p1, p2, weight):

    if weight >= 0:
        color = "green"
    else:
        color = "red"
    width = 0.5 + 2 * abs(weight)

    ax.plot(
        [p1[0], p2[0]],
        [p1[1], p2[1]],
        color=color,
        linewidth=width,
        alpha=0.65,
        zorder=1
    )
    mx = (p1[0] + p2[0]) / 2
    my = (p1[1] + p2[1]) / 2

    ax.text(
        mx,
        my,
        f"{weight:.1f}",
        fontsize=7,
        ha="center",
        va="center",
        bbox=dict(
            facecolor="white",
            alpha=0.7,
            edgecolor="none"
        )
    )

def draw_neuron(ax, position, text):

    circle = Circle(
        position,
        0.55,
        facecolor="lightblue",
        edgecolor="black",
        linewidth=2,
        zorder=3
    )

    ax.add_patch(circle)

    ax.text(
        position[0],
        position[1],
        text,
        ha="center",
        va="center",
        fontsize=8,
        zorder=4
    )

def update(_=None):

    x, W1, b1, W2, b2, activation_name = get_values()

    z1, a1, z2, a2 = forward_propagation(
        x,
        W1,
        b1,
        W2,
        b2,
        activation_name
    )

    network_ax.clear()

    network_ax.set_xlim(0, 10)
    network_ax.set_ylim(0, 10)
    network_ax.axis("off")

    network_ax.set_title(
        "3-3-2 Feedforward Neural Network",
        fontsize=16,
        fontweight="bold"
    )

    for i in range(3):
        for j in range(3):

            draw_connection(
                network_ax,
                input_positions[i],
                hidden_positions[j],
                W1[i, j]
            )

    for i in range(3):
        for j in range(2):

            draw_connection(
                network_ax,
                hidden_positions[i],
                output_positions[j],
                W2[i, j]
            )

    labels = [
        "Methane",
        "Oxygen",
        "Temperature"
    ]

    for i in range(3):

        text = (
            f"{labels[i]}\n"
            f"x={x[i]:.4f}"
        )

        draw_neuron(
            network_ax,
            input_positions[i],
            text
        )

    for i in range(3):

        text = (
            f"H{i+1}\n"
            f"b={b1[i]:.4f}\n"
            f"z={z1[i]:.4f}\n"
            f"a={a1[i]:.4f}"
        )

        draw_neuron(
            network_ax,
            hidden_positions[i],
            text
        )

    output_labels = [
        "SAFE",
        "HAZARD"
    ]

    for i in range(2):

        text = (
            f"{output_labels[i]}\n"
            f"b={b2[i]:.4f}\n"
            f"z={z2[i]:.4f}\n"
            f"score={a2[i]:.4f}"
        )

        draw_neuron(
            network_ax,
            output_positions[i],
            text
        )

    if a2[0] > a2[1]:
        prediction = "SAFE OPERATION"
    else:
        prediction = "HAZARDOUS CONDITION"

    network_ax.text(
        5,
        0.4,
        f"Activation: {activation_name}    "
        f"Prediction: {prediction}",
        ha="center",
        fontsize=14,
        fontweight="bold"
    )

    network_ax.text(
        1.5,
        9.4,
        "INPUT LAYER",
        ha="center",
        fontweight="bold"
    )

    network_ax.text(
        5,
        9.4,
        "HIDDEN LAYER",
        ha="center",
        fontweight="bold"
    )

    network_ax.text(
        8.5,
        9.4,
        "OUTPUT LAYER",
        ha="center",
        fontweight="bold"
    )

    fig.canvas.draw_idle()

def reset(_):
    for slider in input_sliders:
        slider.reset()
    for slider in weight_sliders:
        slider.reset()
    for slider in bias_sliders:
        slider.reset()
    radio.set_active(0)

    update()

def random_input(_):
    random_values = np.random.uniform(
        0,
        1,
        3
    )

    for slider, value in zip(
        input_sliders,
        random_values
    ):
        slider.set_val(
            np.round(value, 2)
        )

for slider in input_sliders:
    slider.on_changed(update)

for slider in weight_sliders:
    slider.on_changed(update)

for slider in bias_sliders:
    slider.on_changed(update)

radio.on_clicked(update)

reset_button.on_clicked(reset)

random_button.on_clicked(random_input)

update()

plt.show()