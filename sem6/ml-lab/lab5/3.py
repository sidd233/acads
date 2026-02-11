import numpy as np

# Given parameters
mu1 = np.array([0.0, 0.0])
mu2 = np.array([3.0, 3.0])
Sigma1 = np.array([[1.1, 0.3], [0.3, 1.9]])
Sigma2 = np.array([[1.0, 0.0], [0.0, 1.0]])

# Equal priors
P1 = 0.5
P2 = 0.5

# Discriminant function
def discriminant(x, mu, Sigma, prior):
    inv_Sigma = np.linalg.inv(Sigma)
    det_Sigma = np.linalg.det(Sigma)

    diff = x - mu
    term1 = -0.5 * diff.T @ inv_Sigma @ diff
    term2 = -0.5 * np.log(det_Sigma)
    term3 = np.log(prior)

    return term1 + term2 + term3

# Classification function
def classify(x):
    g1 = discriminant(x, mu1, Sigma1, P1)
    g2 = discriminant(x, mu2, Sigma2, P2)

    if g1 > g2:
        return "class w1"
    else:
        return "class w2"

# Test vector
x = np.array([1.0, 2.2])
print(classify(x))
