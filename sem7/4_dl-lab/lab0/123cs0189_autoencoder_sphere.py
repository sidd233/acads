import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  

# reproducibility
np.random.seed(42)

# generate 100 uniformly distributed random points on a sphere 
CENTER = np.array([5.0, 5.0, 5.0])
RADIUS = 4.0
N_POINTS = 100

# sampling from a standard normal distribution and normalizing to unit
raw = np.random.normal(size=(N_POINTS, 3))
unit_vectors = raw / np.linalg.norm(raw, axis=1, keepdims=True)
X = CENTER + RADIUS * unit_vectors          # shape (100, 3), original coordinates

# plot 1: Original sphere point cloud
fig = plt.figure(figsize=(7, 6))
ax = fig.add_subplot(111, projection='3d')
ax.scatter(X[:, 0], X[:, 1], X[:, 2], c=X[:, 2], cmap='viridis', s=35, edgecolor='k', linewidth=0.3)
ax.set_title('Original 3D Sphere Point Cloud\n(center=(5,5,5), radius=4, n=100)')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
plt.tight_layout()
plt.savefig('/home/claude/lab/plot1_sphere.png', dpi=150)
plt.close()

# normalize inputs for stable training.
X_norm = (X - CENTER) / RADIUS

# autoencoder architecture: 3 (input) -> 2 (bottleneck) -> 3 (output)
n_in, n_hidden, n_out = 3, 2, 3

rng = np.random.default_rng(42)
W1 = rng.normal(scale=0.5, size=(n_in, n_hidden))
b1 = np.zeros(n_hidden)
W2 = rng.normal(scale=0.5, size=(n_hidden, n_out))
b2 = np.zeros(n_out)

def forward(X_batch):
    z1 = X_batch @ W1 + b1
    h = np.tanh(z1)
    z2 = h @ W2 + b2
    out = z2  # linear output
    return z1, h, out

def mse_loss(pred, target):
    return np.mean((pred - target) ** 2)

# training loop: full-batch gradient descent
EPOCHS = 100
BATCH_SIZE = 100
LR = 0.5

loss_history = []

for epoch in range(EPOCHS):
    # batch_size == dataset size -> the single batch IS the full dataset
    z1, h, out = forward(X_norm)
    loss = mse_loss(out, X_norm)
    loss_history.append(loss)

    # backpropagation (manual gradients of MSE)
    N = X_norm.shape[0]
    d_out = 2.0 * (out - X_norm) / N        

    dW2 = h.T @ d_out                       
    db2 = d_out.sum(axis=0)                 

    d_h = d_out @ W2.T                      
    d_z1 = d_h * (1 - np.tanh(z1) ** 2)     

    dW1 = X_norm.T @ d_z1                   
    db1 = d_z1.sum(axis=0)                  

    # gradient descent update 
    W1 -= LR * dW1
    b1 -= LR * db1
    W2 -= LR * dW2
    b2 -= LR * db2

final_loss_norm = loss_history[-1]

# plot 2: Training loss curve
plt.figure(figsize=(7, 5))
plt.plot(range(1, EPOCHS + 1), loss_history, color='crimson', linewidth=2)
plt.xlabel('Iteration (epoch)')
plt.ylabel('MSE Loss (normalized coordinates)')
plt.title('Autoencoder Training Loss Curve')
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('/home/claude/lab/plot2_loss_curve.png', dpi=150)
plt.close()

# extract latent representations using ONLY the encoder
_, latent, reconstructed_norm = forward(X_norm) 

# plot 3: 2D latent space scatter
plt.figure(figsize=(6.5, 6))
sc = plt.scatter(latent[:, 0], latent[:, 1], c=X[:, 2], cmap='viridis',
                  s=40, edgecolor='k', linewidth=0.3)
plt.colorbar(sc, label='Original Z coordinate')
plt.xlabel('h1 (latent dim 1)')
plt.ylabel('h2 (latent dim 2)')
plt.title('2D Latent Space Representation of Sphere Points')
plt.grid(alpha=0.3)
plt.axis('equal')
plt.tight_layout()
plt.savefig('/home/claude/lab/plot3_latent_space.png', dpi=150)
plt.close()

# final reconstruction loss (MSE) - report in both normalized and original coordinate scales   
reconstructed_original = reconstructed_norm * RADIUS + CENTER
final_mse_original_scale = np.mean((reconstructed_original - X) ** 2)

print("=" * 60)
print("TRAINING SUMMARY")
print("=" * 60)
print(f"Epochs: {EPOCHS} | Batch size: {BATCH_SIZE} | Learning rate: {LR}")
print(f"Final MSE (normalized/unit-sphere coordinates): {final_loss_norm:.6f}")
print(f"Final MSE (original coordinate scale, units^2):  {final_mse_original_scale:.6f}")
print(f"Loss at epoch 1:   {loss_history[0]:.6f}")
print(f"Loss at epoch 100: {loss_history[-1]:.6f}")

# results
with open('/home/claude/lab/results.txt', 'w') as f:
    f.write(f"final_loss_norm={final_loss_norm:.6f}\n")
    f.write(f"final_mse_original_scale={final_mse_original_scale:.6f}\n")
    f.write(f"loss_epoch1={loss_history[0]:.6f}\n")
    f.write(f"loss_epoch100={loss_history[-1]:.6f}\n")

np.save('/home/claude/lab/latent.npy', latent)
np.save('/home/claude/lab/X.npy', X)
np.save('/home/claude/lab/loss_history.npy', np.array(loss_history))

print("\nAll plots saved to /home/claude/lab/")
