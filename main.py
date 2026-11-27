
from datetime import datetime

from etl.extract import (
    extract_students,
    extract_payments
)

from etl.transform import transform_data
from etl.load import load_data


def main():

    # Tao ma cho lan chay ETL
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 50)
    print("STUDENT DATA INTEGRATION SYSTEM")
    print("FULL ETL PIPELINE")
    print("=" * 50)

    # PHASE 1: EXTRACT
    print("\n[PHASE 1] EXTRACT")

    students_df = extract_students(run_id)
    payments_df = extract_payments(run_id)

    print("\nEXTRACT SUMMARY")
    print(f"Students extracted: {len(students_df)}")
    print(f"Payments extracted: {len(payments_df)}")

    # PHASE 2: TRANSFORM
    print("\n[PHASE 2] TRANSFORM")

    transformed_data = transform_data(run_id)

    print("\nTRANSFORM COMPLETED")

    # PHASE 3: LOAD
    print("\n[PHASE 3] LOAD")

    load_result = load_data(run_id)

    # FINAL SUMMARY
    print("\n" + "=" * 50)
    print("ETL PIPELINE SUMMARY")
    print("=" * 50)

    print(f"Run ID: {run_id}")
    print(f"Extracted: {len(students_df) + len(payments_df)}")
    print(
        "Transformed: "
        f"{len(transformed_data['students']) + len(transformed_data['payments'])}"
    )
    print(f"Inserted: {load_result['inserted']}")
    print(f"Updated: {load_result['updated']}")
    print(f"Skipped: {load_result['skipped']}")
    print(f"Rejected: {load_result['rejected']}")
    print(f"Status: {load_result['status']}")

    print("\nETL PIPELINE COMPLETED!")


if __name__ == "__main__":
    main()
