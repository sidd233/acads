import numpy as np
import matplotlib.pyplot as plt

k = 3 # number of classes
n = np.array([50,100,1000]) # dataset sizes
prior = np.array([[0.7,0.2,0.1],[0.9,0.08,0.02]])
estimated_priors = np.zeros((3,2,3))

for x in range(3):
    for y in range(2):
        # generating random dataset
        dataset = np.random.rand(n[x])
        one_hot = np.zeros((n[x],3))

        # setting up integers for counting
        count1 = 0
        count2 = 0
        count3 = 0

        # labelling the data
        for i in range(n[x]):
            if dataset[i] <= prior[y][0]:
                one_hot[i] = [1,0,0]
                count1 = count1 + 1
            elif dataset[i] <= prior[y][0] + prior[y][1]:
                one_hot[i] = [0,1,0]
                count2 = count2 + 1
            else:
                one_hot[i] = [0,0,1]
                count3 = count3 + 1

        # total (should be equal to dataset size)
        total = count2 + count1 + count3

        # calculating estimated class prior probabilities
        estimated_priors[x][y][0] = count1/total
        estimated_priors[x][y][1] = count2/total
        estimated_priors[x][y][2] = count3/total

        print("N = ", n[x])
        print("Prior = ", prior[y])
        print("Number of samples in Class 1 : ",count1)
        print("Number of samples in Class 2 : ",count2)
        print("Number of samples in Class 3 : ",count3)
        print(f"Total (should be equal to {n[x]}) = ",total)

print("Estimated Priors : ", estimated_priors)

# plotting
plt.figure()

for i in range(3):
    plt.plot(
        n,
        estimated_priors[:, 0, i],
        marker='o',
        label=f'Class {i+1}'
    )

plt.hlines(prior[0][0], n[0], n[-1], linestyles='dashed')
plt.hlines(prior[0][1], n[0], n[-1], linestyles='dashed')
plt.hlines(prior[0][2], n[0], n[-1], linestyles='dashed')

plt.xlabel('Dataset size (N)')
plt.ylabel('Estimated class prior')
plt.title('Moderately Imbalanced Class Distribution')
plt.legend()
plt.grid(True)
plt.savefig("q1_1.png")

plt.figure()

for i in range(3):
    plt.plot(
        n,
        estimated_priors[:, 1, i],
        marker='o',
        label=f'Class {i+1}'
    )

plt.hlines(prior[1][0], n[0], n[-1], linestyles='dashed')
plt.hlines(prior[1][1], n[0], n[-1], linestyles='dashed')
plt.hlines(prior[1][2], n[0], n[-1], linestyles='dashed')

plt.xlabel('Dataset size (N)')
plt.ylabel('Estimated class prior')
plt.title('Highly Imbalanced Class Distribution')
plt.legend()
plt.grid(True)
plt.savefig("q1_2.png")
