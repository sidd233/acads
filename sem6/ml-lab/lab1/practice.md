# 🧩 NUMPY — Practice Set (Foundation → ML-level)

### 1️⃣ Vector & statistics

1. Create a NumPy array from 1 to 50

   * Find mean
   * Find standard deviation
   * Find variance
   * Find median

2. Generate 100 random numbers between 0 and 1

   * Count how many are > 0.7
   * Find the max, min

---

### 2️⃣ Matrix operations

3. Create a random 3×3 matrix

   * Find determinant
   * Check if invertible
   * Find inverse

4. Create two 3×3 matrices A and B

   * Compute A+B, A−B
   * Compute A×B (matrix multiplication)

5. Create a 4×4 matrix and verify:
   [
   A \times A^{-1} = I
   ]

---

# 🧩 PANDAS — Practice Set

### 3️⃣ DataFrame creation

6. Create this DataFrame:

| Student | Marks | Attendance |
| ------- | ----- | ---------- |
| Ravi    | 85    | 90         |
| Meera   | 72    | 75         |
| Arjun   | 90    | 95         |
| Kiran   | 60    | 70         |

* Add a column `Result` where:

  * Pass if Marks ≥ 75
  * Fail otherwise

---

### 4️⃣ Filtering & aggregation

7. From the above table:

* Show only students who passed
* Show only students with attendance ≥ 80

8. Find:

* Average marks
* Maximum attendance

---

### 5️⃣ Revenue-style problems (lab-level)

9. Create this DataFrame:

| Product | Price | Quantity |
| ------- | ----- | -------- |
| Pen     | 10    | 50       |
| Book    | 40    | 20       |
| Bag     | 500   | 5        |

* Compute Revenue per product
* Compute total revenue
* Find which product earned the most

---

# 🧩 MATPLOTLIB — Practice Set

### 6️⃣ Line plots

10. Plot:
    [
    y = x^3
    ]
    for x from −5 to 5

11. Plot both:
    [
    y = x^2 \quad \text{and} \quad y = x^3
    ]
    on the same graph.

---

### 7️⃣ Scatter plots (lab-style)

12. Generate 100 random x and y points

* Plot them
* Color points where x > 0.5 differently

13. Generate two clusters:

* 50 points near (2,2)
* 50 points near (7,7)
  Plot them using different markers.

---

# 🔥 COMBO QUESTIONS (NumPy + Pandas + Matplotlib)

These are **one level above your lab**.

### 14

* Generate 100 random (x,y) points using NumPy
* Store them in a Pandas DataFrame
* Compute mean of x and y
* Plot the scatter

---

### 15

* Generate a random 5×5 matrix
* Compute determinant
* Store it in a DataFrame with label
* Plot determinant values of 10 such matrices

