from pathlib import Path
from datetime import datetime

import pandas as pd
from sqlalchemy import text

from config import BASE_DIR, create_source_engine


# KHOI TAO THU MUC


SOURCE_DIR = BASE_DIR / "data" / "source"
EXTRACTED_DIR = BASE_DIR / "data" / "extracted"


def create_run_directory(run_id):

    # Tao thu muc rieng cho moi lan Extract.

    run_dir = EXTRACTED_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    return run_dir


# EXTRACT 1: DOC DU LIEU CSV


def extract_students(run_id):
    """
    Doc du lieu sinh vien tu file CSV.
    Khong chuan hoa hoac thay doi gia tri nguon.
    """

    input_file = SOURCE_DIR / "students.csv"

    if not input_file.exists():
        raise FileNotFoundError(
            f"Khong tim thay file: {input_file}"
        )

    required_columns = [
        "student_code",
        "full_name",
        "date_of_birth",
        "class",
        "email"
    ]

    df = pd.read_csv(
        input_file,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig"
    )

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"CSV thieu cac cot bat buoc: {missing_columns}"
        )

    run_dir = create_run_directory(run_id)

    output_file = run_dir / "students_extracted.csv"

    df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n===== EXTRACT STUDENTS =====")
    print(f"Nguon: {input_file}")
    print(f"So ban ghi: {len(df)}")
    print(f"So cot: {len(df.columns)}")
    print(f"Da luu: {output_file}")

    return df


# EXTRACT 2: DOC DU LIEU MYSQL

def extract_payments(run_id):
    """
    Truy xuat du lieu thanh toan tu MySQL.
    Khong chinh sua du lieu nguon.
    """

    engine = create_source_engine()

    query = text("""
        SELECT
            source_row_id,
            payment_id,
            student_code,
            amount,
            payment_date,
            status,
            extracted_at
        FROM raw_payments
        ORDER BY source_row_id
    """)

    try:
        with engine.connect() as connection:

            df = pd.read_sql_query(
                query,
                connection
            )

        run_dir = create_run_directory(run_id)

        output_file = run_dir / "payments_extracted.csv"

        df.to_csv(
            output_file,
            index=False,
            encoding="utf-8-sig"
        )

        print("\n===== EXTRACT PAYMENTS =====")
        print("Database: payment_source")
        print("Table: raw_payments")
        print(f"So ban ghi: {len(df)}")
        print(f"So cot: {len(df.columns)}")
        print(f"Da luu: {output_file}")

        return df

    finally:
        engine.dispose()

# CHAY THU RIENG MODULE

if __name__ == "__main__":

    run_id = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    students_df = extract_students(run_id)
    payments_df = extract_payments(run_id)

    print("\n===== EXTRACT SUMMARY =====")
    print(f"Run ID: {run_id}")
    print(f"Students: {len(students_df)}")
    print(f"Payments: {len(payments_df)}")
    print("EXTRACT HOAN THANH!")
