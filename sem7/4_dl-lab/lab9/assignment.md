# Deep Learning Laboratory Assignment – 9

## Objective

Investigate how learned convolutional filters in a trained LeNet-style CNN respond to input images by identifying their Top-8 maximally activating images, locating the strongest spatial response, tracing the corresponding theoretical receptive field to the original image, and comparing feature representations between Conv1 and Conv2.

## 1. Fixed Dataset and CNN Configuration

Use MNIST dataset and the following fixed LeNet-style architecture:

**Input (1 × 28 × 28) → Conv1 (1→6, 5×5) → ReLU → AveragePool (2×2) → Conv2 (6→16, 5×5) → ReLU → AveragePool (2×2) → FC1 (256→120) → ReLU → FC2 (120→84) → ReLU → FC3 (84→10).**

Stage and output dimension:

**Input (1×28×28) → Conv1 (6×24×24) → ReLU (6×24×24) → AvgPool (6×12×12) → Conv2 (16×8×8) → ReLU (16×8×8) → AvgPool (16×4×4) → Flatten (256) → FC1 (120) → ReLU (120) → FC2 (84) → ReLU (84) → FC3 (10).**

Conv1 has 6 filters and Conv2 has 16 filters; visualization is performed only for these two convolutional layers. Use filter numbers 1–6 and 1–16, respectively. Training: Cross-Entropy Loss, SGD (LR = 0.01, momentum = 0.9), batch size = 64, epochs = 10, seed = 42, PyTorch default initialization. The model must achieve ≥97% test accuracy. Use `model.eval()` for testing/visualization and the instructor-provided checkpoint for Experiments 2–6 without modification.

## 2. Required CNN Terminology

A filter is a learned convolution kernel. A feature map is the spatial output produced by one filter. An individual convolutional neuron is one element of a feature map, $A[c,y,x]$. An activation is the numerical response of a neuron. PRE-ReLU activation is the raw convolution output $Z$; POST-ReLU activation is $A = \max(0,Z)$. The theoretical receptive field of a neuron is the region of the original input that can influence that neuron according to the network architecture. A receptive field is not a causal attribution map and does not prove that every pixel in the region caused the response. A classification output is the final class evidence produced by the classifier.

## 3. Interactive CNN Visualization Tool

Use the provided interactive CNN visualization tool with the fixed LeNet checkpoint. For each experiment, select the specified layer/filter and activation mode, scan the complete MNIST test set, and report the Top-8 results. The visualization must show the original image, ground-truth digit, activation value, maximum activation location, theoretical receptive-field region, and corresponding receptive-field crop.

## 4. Definition of the Maximally Activating Image

For test image $i$ and selected filter $c$, let $A_i(c,y,x)$ denote the POST-ReLU feature map. Define the image-level activation score as

$$
S_i = \max_{y,x} A_i(c,y,x).
$$

The maximum-response location is

$$
(y_i^*, x_i^*) = \operatorname*{arg\,max}_{y,x} A_i(c,y,x).
$$

Rank all 10,000 MNIST test images by $S_i$ in descending order. The Top-8 maximally activating images are the eight test images with the largest $S_i$ values. This is a filter-level experiment: the same selected filter is evaluated across all images, while the spatial location of its strongest response may differ from image to image.

## 5. Experiment 1 – Train and Verify the LeNet-style CNN Model

Train the LeNet-style CNN model using the fixed configuration. Record epoch-wise training loss and training accuracy, final test accuracy, and the output dimensions after each convolutional and pooling layer. Verify that the model achieves at least 97% test accuracy before proceeding.

## 6. Experiment 2 – Maximally Activating Images of a Conv1 Filter

Use the instructor-assigned Conv1 filter. Use POST-ReLU activation and scan all 2,000 MNIST test images. Identify the Top-8 images using the definition above. For each image, report the ground-truth digit, activation score, maximum-response location, and receptive-field region. Describe the visual characteristics shared by the corresponding patches.

## 7. Experiment 3 – Conv1 versus Conv2 Filter Responses

Repeat the maximally activating image analysis for the instructor-assigned Conv2 filter. Compare Conv1 and Conv2 in terms of theoretical receptive-field size, activated regions, visual-pattern complexity, and Top-8 digit distribution.

Discuss what evidence supports a change in representation from the first to the second convolutional layer. Do not assume that Conv2 filters must represent complete digits.

## 8. Experiment 4 – Filter Selectivity Across Digit Classes

Use three instructor-assigned filters from Conv1 and three from Conv2. For each filter, analyze the Top-8 digit labels and activation strengths and classify the filter as predominantly class-associated (at least 6 of 8 images have the same digit), multi-class (at least 3 digit classes occur with no single class having 6 or more images), or shared visual pattern when a common pattern is evident in the receptive-field patches across different digit classes.

Report the filter number, Top-8 digit distribution, activation values, and interpretation, supporting all visual-pattern claims with the displayed receptive-field patches.

## 9. Experiment 5 – Mathematical Receptive-Field Analysis

Calculate the theoretical receptive-field size of selected Conv1 and Conv2 neurons. Use $r_0 = 1$ and jump $j_0 = 1$. For a layer with kernel size $k$ and stride $s$:

$$
r_l = r_{l-1} + (k_l - 1)j_{l-1}
$$

and

$$
j_l = j_{l-1}s_l.
$$

For this architecture, verify: Conv1 RF = 5×5; after S2 RF = 6×6; Conv2 RF = 14×14; after S4 RF = 16×16.

Compare the theoretical RF with the corresponding region shown in the original image. If a theoretical RF extends beyond the image boundary, report both the theoretical RF size and its visible intersection with the 28×28 image.

## 10. Experiment 6 – PRE-ReLU versus POST-ReLU Activation

For one instructor-assigned convolutional filter, compare PRE-ReLU activation $Z$ and POST-ReLU activation $A = \max(0,Z)$.

Define

$$
S_i^{\mathrm{pre}} = \max_{y,x} z_i(c,y,x)
$$

and

$$
S_i^{\mathrm{post}} = \max_{y,x} A_i(c,y,x).
$$

Compare the Top-8 images, activation values, maximum-response locations, and interpretations.

If all PRE-ReLU values for an image are negative, the maximum is still negative; it represents the least-negative response and must not be described as a positive activation. Explain how ReLU removes negative responses and why POST-ReLU values are convenient for interpreting positive feature responses.

## 11. Required Results

Prepare one consolidated table containing at least the following fields:

| Layer | Filter | Activation mode | Top-1 digit | Top-1 activation | Top-1 location | RF size | Top-8 digit distribution |
|---|---|---|---|---|---|---|---|
| Conv1 | … | POST-ReLU | … | … | (y,x) | 5×5 | … |
| Conv2 | … | POST-ReLU | … | … | (y,x) | 14×14 | … |

Generate exactly three consolidated figures (each figure may contain multiple panels):

1. Top-8 maximally activating images for the selected Conv1 filter;
2. Top-8 maximally activating images and receptive fields for the selected Conv2 filter; and
3. comparison of filter selectivity across digit classes.

Every Top-8 visualization must identify the maximum activation location and corresponding receptive-field region.

Submit the source code, the trained LeNet model checkpoint, the consolidated results table, three required figures, training/test accuracy results, receptive-field calculations, and PRE-ReLU versus POST-ReLU comparison with brief interpretations.