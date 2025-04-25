import pandas as pd

df = pd.read_csv("data/values.csv")

res = df[df["ingredient"] == "Salt"]["effect"]

print(res)

for eff in res:
    print(eff)
