import pandas as pd

a = [
    ["Alice", 24, "New York"],
    ["Bob", 30, "Chicago"],
    ["Charlie", 29, "San Francisco"],
    ["David", 35, "NYC"]
]

df = pd.DataFrame(a, columns=["Name", "Age", "City"])
# print(df)

df_filtered = df[df["Age"]>28]
print(df_filtered)