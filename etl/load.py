
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from config import BASE_DIR, create_target_engine


TRANSFORMED_DIR = BASE_DIR / "data" / "transformed"
EXTRACTED_DIR = BASE_DIR / "data" / "extracted"


def read_csv_file(file_path):
    """Read a transformed CSV file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Khong tim thay file: {file_path}")

    return pd.read_csv(
        file_path,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig"
    )


def normalize_student_record(record):
    return {
        "student_id": record["student_id"].strip().upper(),
        "full_name": record["full_name"].strip(),
        "date_of_birth": date.fromisoformat(record["date_of_birth"]),
        "class_name": record["class_name"].strip(),
        "email": record["email"].strip() or None
    }


def normalize_payment_record(record):
    return {
        "payment_id": record["payment_id"].strip().upper(),
        "student_id": record["student_id"].strip().upper(),
        "amount": Decimal(record["amount"]).quantize(Decimal("0.01")),
        "payment_date": datetime.strptime(
            record["payment_date"],
            "%Y-%m-%d %H:%M:%S"
        ),
        "status": record["status"].strip().upper()
    }


def student_records_equal(existing, incoming):
    return (
        existing["full_name"] == incoming["full_name"]
        and existing["date_of_birth"] == incoming["date_of_birth"]
        and existing["class_name"] == incoming["class_name"]
        and existing["email"] == incoming["email"]
    )


def payment_records_equal(existing, incoming):
    existing_amount = Decimal(str(existing["amount"])).quantize(
        Decimal("0.01")
    )

    return (
        existing["student_id"] == incoming["student_id"]
        and existing_amount == incoming["amount"]
        and existing["payment_date"] == incoming["payment_date"]
        and existing["status"] == incoming["status"]
    )


def load_students(connection, students_df):
    inserted = 0
    updated = 0
    skipped = 0

    for raw_record in students_df.to_dict(orient="records"):
        record = normalize_student_record(raw_record)

        existing = connection.execute(
            text("""
                SELECT student_id, full_name, date_of_birth,
                       class_name, email
                FROM students
                WHERE student_id = :student_id
            """),
            {"student_id": record["student_id"]}
        ).mappings().first()

        if existing is None:
            connection.execute(
                text("""
                    INSERT INTO students (
                        student_id, full_name, date_of_birth,
                        class_name, email
                    )
                    VALUES (
                        :student_id, :full_name, :date_of_birth,
                        :class_name, :email
                    )
                """),
                record
            )
            inserted += 1

        elif student_records_equal(existing, record):
            skipped += 1

        else:
            connection.execute(
                text("""
                    UPDATE students
                    SET full_name = :full_name,
                        date_of_birth = :date_of_birth,
                        class_name = :class_name,
                        email = :email
                    WHERE student_id = :student_id
                """),
                record
            )
            updated += 1

    return inserted, updated, skipped


def load_payments(connection, payments_df):
    inserted = 0
    skipped = 0
    conflicts = []

    for raw_record in payments_df.to_dict(orient="records"):
        record = normalize_payment_record(raw_record)

        existing = connection.execute(
            text("""
                SELECT payment_id, student_id, amount,
                       payment_date, status
                FROM payments
                WHERE payment_id = :payment_id
            """),
            {"payment_id": record["payment_id"]}
        ).mappings().first()

        if existing is None:
            connection.execute(
                text("""
                    INSERT INTO payments (
                        payment_id, student_id, amount,
                        payment_date, status
                    )
                    VALUES (
                        :payment_id, :student_id, :amount,
                        :payment_date, :status
                    )
                """),
                record
            )
            inserted += 1

        elif payment_records_equal(existing, record):
            skipped += 1

        else:
            conflicts.append({
                "source_name": "payments",
                "record_identifier": record["payment_id"],
                "raw_data": json.dumps(
                    raw_record,
                    ensure_ascii=False,
                    default=str
                ),
                "rejection_reason": (
                    "Xung dot khi Load: payment_id da ton tai "
                    "nhung noi dung giao dich khac"
                )
            })

    return inserted, skipped, conflicts


def save_rejected_records(connection, run_id, rejected_records):
    for record in rejected_records:
        raw_data = record.get("raw_data", "{}")

        # raw_data tu Transform da la JSON string.
        # Kiem tra de dam bao du lieu hop le truoc khi ghi vao MySQL.
        try:
            json.loads(raw_data)
        except (TypeError, json.JSONDecodeError):
            raw_data = json.dumps(
                raw_data,
                ensure_ascii=False,
                default=str
            )

        connection.execute(
            text("""
                INSERT INTO rejected_records (
                    run_id,
                    source_name,
                    record_identifier,
                    raw_data,
                    rejection_reason
                )
                VALUES (
                    :run_id,
                    :source_name,
                    :record_identifier,
                    :raw_data,
                    :rejection_reason
                )
            """),
            {
                "run_id": run_id,
                "source_name": record.get("source_name", "unknown"),
                "record_identifier": (
                    record.get("record_identifier") or None
                ),
                "raw_data": raw_data,
                "rejection_reason": record["rejection_reason"]
            }
        )


def save_data_quality_results(
    connection,
    run_id,
    students_input_count,
    payments_input_count,
    students_valid_count,
    payments_valid_count,
    rejected_records
):
    students_rejected = sum(
        1 for record in rejected_records
        if record.get("source_name") == "students"
    )

    payments_rejected = sum(
        1 for record in rejected_records
        if record.get("source_name") == "payments"
    )

    quality_results = [
        {
            "source_name": "students",
            "rule_name": "validation_and_deduplication",
            "total_checked": students_input_count,
            "passed_count": students_valid_count,
            "failed_count": students_rejected
        },
        {
            "source_name": "payments",
            "rule_name": "validation_and_deduplication",
            "total_checked": payments_input_count,
            "passed_count": payments_valid_count,
            "failed_count": payments_rejected
        }
    ]

    for result in quality_results:
        connection.execute(
            text("""
                INSERT INTO data_quality_results (
                    run_id,
                    source_name,
                    rule_name,
                    total_checked,
                    passed_count,
                    failed_count
                )
                VALUES (
                    :run_id,
                    :source_name,
                    :rule_name,
                    :total_checked,
                    :passed_count,
                    :failed_count
                )
            """),
            {
                "run_id": run_id,
                **result
            }
        )


def load_data(run_id):
    run_dir = TRANSFORMED_DIR / run_id
    extracted_dir = EXTRACTED_DIR / run_id

    students_file = run_dir / "students_transformed.csv"
    payments_file = run_dir / "payments_transformed.csv"
    rejected_file = run_dir / "rejected_records.csv"

    # Doc lai cac file dau ra cua Transform.
    students_df = read_csv_file(students_file)
    payments_df = read_csv_file(payments_file)
    rejected_df = read_csv_file(rejected_file)

    # Dem so ban ghi dau vao tu Extract.
    students_extracted = read_csv_file(
        extracted_dir / "students_extracted.csv"
    )
    payments_extracted = read_csv_file(
        extracted_dir / "payments_extracted.csv"
    )

    # Chuyen rejected DataFrame thanh list dictionary.
    rejected_records = rejected_df.to_dict(orient="records")

    engine = create_target_engine()

    # Tao run record rieng va commit truoc khi Load.
    # Neu Load that bai, van giu duoc lich su FAILED.
    try:
        with engine.begin() as connection:
            result = connection.execute(
                text("""
                    INSERT INTO etl_runs (
                        status,
                        extracted_count,
                        transformed_count,
                        rejected_count
                    )
                    VALUES (
                        'RUNNING', :extracted_count,
                        :transformed_count, :rejected_count
                    )
                """),
                {
                    "extracted_count": (
                        len(students_extracted)
                        + len(payments_extracted)
                    ),
                    "transformed_count": (
                        len(students_df) + len(payments_df)
                    ),
                    "rejected_count": len(rejected_records)
                }
            )

            database_run_id = result.lastrowid

        try:
            # Toan bo thao tac Load nam trong mot transaction.
            with engine.begin() as connection:

                student_inserted, student_updated, student_skipped = (
                    load_students(connection, students_df)
                )

                (
                    payment_inserted,
                    payment_skipped,
                    payment_conflicts
                ) = load_payments(connection, payments_df)

                # Them cac xung dot phat sinh trong Load vao danh sach reject.
                all_rejected = rejected_records + payment_conflicts

                save_rejected_records(
                    connection,
                    database_run_id,
                    all_rejected
                )

                save_data_quality_results(
                    connection,
                    database_run_id,
                    len(students_extracted),
                    len(payments_extracted),
                    len(students_df),
                    len(payments_df),
                    rejected_records
                )

                inserted_count = student_inserted + payment_inserted
                updated_count = student_updated
                skipped_count = student_skipped + payment_skipped

                final_status = (
                    "PARTIAL" if all_rejected else "SUCCESS"
                )

                connection.execute(
                    text("""
                        UPDATE etl_runs
                        SET finished_at = NOW(),
                            status = :status,
                            inserted_count = :inserted_count,
                            updated_count = :updated_count,
                            skipped_count = :skipped_count,
                            rejected_count = :rejected_count
                        WHERE run_id = :run_id
                    """),
                    {
                        "status": final_status,
                        "inserted_count": inserted_count,
                        "updated_count": updated_count,
                        "skipped_count": skipped_count,
                        "rejected_count": len(all_rejected),
                        "run_id": database_run_id
                    }
                )

            print("\n" + "=" * 50)
            print("LOAD RESULT")
            print("=" * 50)
            print(f"Database Run ID: {database_run_id}")
            print(f"Students inserted: {student_inserted}")
            print(f"Students updated: {student_updated}")
            print(f"Students skipped: {student_skipped}")
            print(f"Payments inserted: {payment_inserted}")
            print(f"Payments skipped: {payment_skipped}")
            print(f"Payment conflicts: {len(payment_conflicts)}")
            print(f"Total rejected: {len(all_rejected)}")
            print(f"Final status: {final_status}")
            print("\nLOAD SUCCESS!")

            return {
                "run_id": database_run_id,
                "status": final_status,
                "inserted": inserted_count,
                "updated": updated_count,
                "skipped": skipped_count,
                "rejected": len(all_rejected)
            }

        except Exception:
            # Transaction Load da rollback.
            # Cap nhat trang thai FAILED bang transaction moi.
            with engine.begin() as connection:
                connection.execute(
                    text("""
                        UPDATE etl_runs
                        SET finished_at = NOW(),
                            status = 'FAILED'
                        WHERE run_id = :run_id
                    """),
                    {"run_id": database_run_id}
                )

            raise

    finally:
        engine.dispose()
