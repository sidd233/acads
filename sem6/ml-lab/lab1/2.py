import numpy as np
a = np.array([[2,2,3],[4,5,6],[7,8,9]])
a_inv = np.linalg.inv(a)

print(np.dot(a,a_inv))