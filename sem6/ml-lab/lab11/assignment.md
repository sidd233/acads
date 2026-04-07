python3 -m venv my-env && source my-env/bin/activate && pip install numpy pandas matplotlib scikit-learn

# **Lab Assignment 10**

## **Topic: Clustering Techniques (K-Means and DBSCAN)**

---

## **Question 1: K-Means Implementation and Analysis**

Implement the K-Means clustering algorithm from scratch *(without using built-in clustering functions)*.

### **Tasks:**

1. Generate a 2D synthetic dataset *(e.g., using `make_blobs`)*.

2. Run the algorithm for different values of **K** *(e.g., K = 2, 3, 4, 5)*.

3. Plot the clusters along with their corresponding centroids.

4. Compute the **Within-Cluster Sum of Squares (WCSS)**:

   ```
   WCSS = Σ (i=1 to K) Σ (x ∈ Cᵢ) ||x - μᵢ||²
   ```

5. Use the **Elbow Method** to determine the optimal number of clusters.

### **Expected Outcome:**

* Understanding of centroid initialization
* Convergence behavior
* Cluster compactness

---

## **Question 2: K-Means vs DBSCAN (Comparative Study)**

Use the non-spherical clusters dataset `make_moons`.

### **Tasks:**

1. Apply **K-Means clustering** and visualize the results.

2. Apply **DBSCAN clustering** with suitable values of **ε (epsilon)** and **min_samples**.

3. Compare the clustering outputs:

   * Visually
   * Quantitatively

4. Discuss:

   * Limitations of K-Means for non-linear cluster shapes
   * How DBSCAN handles noise and irregular clusters

### **Expected Outcome:**

* Understanding strengths and weaknesses of different clustering techniques

---

## **Question 3: DBSCAN Parameter Sensitivity Analysis**

Use a standard library *(e.g., `sklearn`)* to implement DBSCAN.

### **Tasks:**

1. Apply DBSCAN on a dataset of your choice.

2. Experiment with different values of:

   * **ε (epsilon)** – neighborhood radius
   * **min_samples**

3. Plot clustering results for each parameter setting.

4. Identify:

   * Core Points
   * Border Points
   * Noise Points

5. Analyze how parameter changes affect cluster formation.

### **Expected Outcome:**

* Insight into density-based clustering behavior
* Understanding parameter tuning

---

## **Question 4: Real-World Dataset Clustering**

Select the **Customer Segmentation dataset** from Kaggle.

### **Tasks:**

1. Perform **data preprocessing**:

   * Handle missing values
   * Normalize data

2. Apply:

   * **K-Means clustering**
   * **DBSCAN clustering**

3. Evaluate clustering quality using:

   * **Silhouette Score**
   * Visualization *(2D/3D as applicable)*

4. Provide a **comparative analysis**:

   * Which algorithm performs better and why?
   * Practical interpretation of clusters

### **Expected Outcome:**

* Ability to apply clustering techniques to real-world datasets
* Interpretation of clustering results
