
from pathlib import Path

import pandas as pd

from config import BASE_DIR
from etl.load import load_data


TRANSFORMED_DIR = BASE_DIR / "data" / "transformed"

# Tim thu muc Transform gan nhat
run_dirs = sorted(
    [path for path in TRANSFORMED_DIR.iterdir() if path.is_dir()],
    key=lambda path: path.name
)

if not run_dirs:
    raise FileNotFoundError("Khong tim thay thu muc Transformed")

run_dir = run_dirs[-1]
run_id = run_dir.name

students_file = run_dir / "students_transformed.csv"

# Sao luu noi dung file goc de khoi phuc
original_content = students_file.read_bytes()

try:
    students_df = pd.read_csv(
        students_file,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig"
    )

    # Tim sinh vien SV001
    mask = students_df["student_id"] == "SV001"

    if not mask.any():
        raise ValueError("Khong tim thay SV001 trong file Transform")

    original_class = students_df.loc[
        mask, "class_name"
    ].iloc[0]

    test_class = original_class + "_TEST"

    # Thay doi tam thoi thong tin lop
    students_df.loc[mask, "class_name"] = test_class

    students_df.to_csv(
        students_file,
        index=False,
        encoding="utf-8-sig"
    )

    print("=" * 50)
    print("TEST UPDATE STUDENT")
    print("=" * 50)
    print(f"Run ID: {run_id}")
    print(f"Student: SV001")
    print(f"Original class: {original_class}")
    print(f"Test class: {test_class}")

    # Load du lieu da thay doi
    print("\n[1] LOAD MODIFIED STUDENT")
    first_result = load_data(run_id)

    print("\nUpdate test result:")
    print(first_result)

finally:
    # Luon khoi phuc file Transform goc
    students_file.write_bytes(original_content)

# Load lai du lieu goc de khoi phuc database
print("\n[2] RESTORE ORIGINAL STUDENT DATA")
restore_result = load_data(run_id)

print("\nRestore result:")
print(restore_result)

print("\nTEST COMPLETED")
