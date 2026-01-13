import pandas as pd

df = pd.read_csv("/Users/kirenp/kiren2/projects_inprogress/2026_projects/Data Engineering Apprenticeship/projects/stage_1/data/raw_customers.csv")
df["age"] = pd.to_numeric(df["age"], errors="coerce") # This converts column to float
df["age"] = df["age"].fillna(0).astype(int)  # Replace NaN with 0, then convert to int

#df.to_csv("/Users/kirenp/kiren2/projects_inprogress/2026_projects/Data Engineering Apprenticeship/projects/stage_1/data/raw_customers_cleaned.csv", index=False)