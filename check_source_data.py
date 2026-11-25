import pandas as pd

df = pd.read_csv(
    "data/source/students.csv",
    dtype=str,
    keep_default_na=False
)

print("TONG SO DONG:", len(df))
print("\nCAC COT:")
print(df.columns.tolist())

print("\n8 DONG DAU:")
print(df.head(8))

print("\nSO MA SINH VIEN TRUNG:")
print(df["student_code"].str.strip().str.upper().duplicated().sum())