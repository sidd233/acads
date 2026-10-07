# Deep Learning Laboratory Assignment – 8
Investigate empirically how selected modifications to an AlexNet-style architecture affect
image-classification performance, convergence, generalization, parameter count, and
computational cost under a fixed training configuration.

## Dataset and Fixed Experimental Setup
Use the CIFAR-10 dataset. Select 12,000 training samples and 2,000 validation samples from the
original training set, and 2,000 test samples from the original test set, using a fixed random seed
of 42, Use a fixed random generator for DataLoader shuffling and use the same generator seed
for all experiments. Use the same samples and split for all experiments. Resize all images to 64 ×
64 and normalize them using Mean = (0.4914, 0.4822, 0.4465) and Standard Deviation = (0.2470,
0.2435, 0.2616). Do not use data augmentation. Implement the AlexNet-style model manually
using PyTorch layers. Do not use pretrained weights or directly import AlexNet from
torchvision.models. Use Cross-Entropy Loss, Adam optimizer with learning rate = 0.001, batch size
= 64, 10 epochs, and random seed = 42. Use PyTorch default weight initialization and reset the
random seed to 42 before initializing each model. Use model.eval() during validation and testing.
For all experiments, keep the dataset split, preprocessing, optimizer, learning rate, batch size,
number of epochs, loss function, initialization procedure, and evaluation procedure identical. Do
not tune individual models separately. Use Google Colab GPU for training and report the
measured training time for each model.

## Baseline AlexNet for 64 × 64 Input
Use the following AlexNet-style architecture:
Conv(3→32, 5×5, stride=1, padding=2) → ReLU → MaxPool(2×2) → Conv(32→64, 5×5, stride=1,
padding=2) → ReLU → MaxPool(2×2) → Conv(64→128, 3×3, padding=1) → ReLU →
Conv(128→128, 3×3, padding=1) → ReLU → Conv(128→128, 3×3, padding=1) → ReLU →
MaxPool(2×2) → Flatten → FC(8192→512) → ReLU → Dropout(0.5) → FC(512→256) → ReLU →
Dropout(0.5) → FC(256→10).
For a 64 × 64 input, the spatial dimensions change as 64 × 64 → 32 × 32 → 16 × 16 → 8 × 8,
giving a flattened feature size of 128 × 8 × 8 = 8192.

### Experiment 1 – Baseline AlexNet Performance
Train the baseline AlexNet for 10 epochs using the fixed experimental configuration. Observe the
epoch-wise training and validation behavior and assess whether the model shows evidence of
underfitting, overfitting, or reasonably stable generalization. Discuss whether the model appe ars
to have converged within the 10-epoch training budget.

### Experiment 2 – Effect of Classifier Size
Modify only the fully connected classifier to: 8192 → 256 → 128 → 10. Keep all convolutional
layers, dropout, and training settings unchanged. Compare training accuracy, validation accuracy,
training loss, validation loss, generalization gap, parameter count, and training time. Analyze
whether reducing the classifier size lowers model complexity while maintaining similar predictive
performance. Discuss what the result suggests about the contribution of the fully connected
classifier to overall model capacity.

### Experiment 3 – Effect of Convolutional Width
Starting again from the baseline architecture, reduce the number of convolutional filters as
follows:
Conv1: 3 → 16
Conv2: 16 → 32
Conv3: 32 → 64
Conv4: 64 → 64
Conv5: 64 → 64
Keep the kernel sizes, strides, padding, pooling operations, optimizer, learning rate, batch size,
dropout rate, and number of epochs unchanged.
For the 64 × 64 input, the final feature-map size is 64 × 8 × 8. Therefore, use the classifier:
Flatten(4096) → FC(512) → ReLU → Dropout(0.5) → FC(256) → ReLU → Dropout(0.5) → FC(10)
Investigate how reducing convolutional width affects model capacity, generalization, and
computational requirements compared with the baseline architecture.

## Required Results
Prepare one consolidated table comparing the baseline AlexNet, reduced-classifier model, and
reduced-width model using final training accuracy, validation accuracy, final test accuracy, final
training loss, final validation loss, generalization gap, number of trainable parameters, and
measured training time. Use the validation results for experimental comparison and
interpretation. The test set must be used only for final evaluation and should not be used to select
or tune a model.
Generate a maximum of three plots:
1. Training and validation accuracy versus epoch.
2. Training and validation loss versus epoch.
3. Validation accuracy versus number of trainable parameters.
Based on the results, analyze the effects of reducing classifier size and convolutional width on
generalization, model complexity, and computational cost. Propose one additional AlexNet-style
modification that may improve the accuracy–computation trade-off without training the
proposed model. Explain the expected effect of the proposed modification.

## Submission Requirements
Submit the Python source code or Jupyter Notebook, the consolidated results table, a maximum
of three plots, and a concise 1–2 page analysis.