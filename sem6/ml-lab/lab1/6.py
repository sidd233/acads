import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

np.random.seed(0)

x = np.random.rand(50)
y = np.random.rand(50)

plt.scatter(x[x<0.5], y[x<0.5], marker='o', c='blue', label='x < 0.5')
plt.scatter(x[x>=0.5], y[x>=0.5], marker='^', c='red', label='x ≥ 0.5')

plt.xlabel("x")
plt.ylabel("y")
plt.title("Scatter Plot with Two Ranges")
plt.legend()

plt.savefig("plot.png")

x_mean = pd.DataFrame(x).mean()
y_mean = pd.DataFrame(y).mean()
print("mean of x = ",x_mean)
print("mean of y = ",y_mean)