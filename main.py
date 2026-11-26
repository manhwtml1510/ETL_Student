
from datetime import datetime

from etl.extract import (
    extract_students,
    extract_payments
)


def main():

    # Tao ma cho lan chay ETL
    run_id = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    print("=" * 50)
    print("STUDENT DATA INTEGRATION SYSTEM")
    print("ETL - EXTRACT PHASE")
    print("=" * 50)

    # Buoc 1: Extract CSV
    students_df = extract_students(run_id)

    # Buoc 2: Extract MySQL
    payments_df = extract_payments(run_id)

    # Tong ket
    print("\n" + "=" * 50)
    print("EXTRACT RESULT")
    print("=" * 50)

    print(f"Run ID: {run_id}")
    print(f"Students extracted: {len(students_df)}")
    print(f"Payments extracted: {len(payments_df)}")

    print("\nEXTRACT SUCCESS!")


if __name__ == "__main__":
    main()
