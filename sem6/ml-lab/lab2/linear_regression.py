import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("Real_Estate.csv")

# columns in data set:
# 'Transaction date', 'House age', 'Distance to the nearest MRT station', 'Number of convenience stores', 'Latitude', 'Longitude', 'House price of unit area'

# defining dependent and independent variables
Y = df[["House price of unit area"]].values
X = df[["House age","Distance to the nearest MRT station", "Number of convenience stores", "Latitude","Longitude"]].values
# print(X.shape)

# defining loss(error) function
def loss_function(m, b, x, y):
    error_array = y - (m*x+b) # PROBLEM: there's more than one independent variable, need to take each into account, consider m to be a 1D matrix of coefficients, same with b
    squared_error = error_array**2
    sum_squared_error = squared_error.sum()
    mse = sum_squared_error/float(len(y))
    return mse