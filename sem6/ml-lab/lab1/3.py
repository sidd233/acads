import numpy as np
import matplotlib.pyplot as plt

# generates 400 equally spaced x-values from –10 to +10
x = np.linspace(-10, 10, 400)
y = x**2

plt.plot(x, y)
plt.xlabel("x")
plt.ylabel("y")
plt.title("y = x^2")

plt.savefig("plot.png")
