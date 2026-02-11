import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# NUMPY — Practice Set
# 1. Vector & statistics
# a = np.linspace(1,50,50) # creates float values
a = np.arange(1, 51) # creates integer values
# print(a) # for testing
mean = np.mean(a)
variance = np.var(a)
median = np.median(a)
sd = np.sqrt(variance)
print("Mean = ",mean,"\nVariance = ",variance,"\nMedian = ",median,"\nStandard Deviation = ",sd)