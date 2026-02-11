import pandas as pd

df = pd.DataFrame([["A",50,10],["B",30,5],["C",40,8]],columns=["Product","Price","Quantity"])

df["Revenue"] = df["Price"] * df["Quantity"]

print(df)
total_revenue = df["Revenue"].sum()
print("Total Revenue = ",total_revenue)