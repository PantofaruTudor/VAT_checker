import pandas as pd

df = pd.read_csv("preview.csv", dtype=str)
df.columns = df.columns.str.strip()
print(df.iloc[1].dropna().to_string())
