
import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd


# xác định các thư mục dữ liệu, regex patterns và các hàm tiện ích dùng chung cho việc transform dữ liệu.

BASE_DIR = Path(__file__).resolve().parent.parent

EXTRACTED_DIR = BASE_DIR / "data" / "extracted"
TRANSFORMED_DIR = BASE_DIR / "data" / "transformed"

STUDENT_CODE_PATTERN = re.compile(r"^SV\d{3}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

ALLOWED_PAYMENT_STATUSES = {
    "PAID",
    "PENDING",
    "FAILED",
}


# chuẩn hóa dữ liệu, các hàm tiện ích được định nghĩa để làm sạch văn bản, phân tích ngày tháng và tạo các bản ghi bị từ chối.

def clean_text(value):
    # Remove leading/trailing spaces and collapse repeated spaces.
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def parse_date(value):
    # Convert supported date formats into a date object.
    value = clean_text(value)

    if not value:
        raise ValueError("Ngày tháng bị bỏ trống")

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Ngày tháng không hợp lệ: {value}")


def parse_payment_datetime(value):
    # Convert supported payment date formats into datetime.
    value = clean_text(value)

    if not value:
        raise ValueError("Ngày thanh toán bị bỏ trống")

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise ValueError(f"Ngày thanh toán không hợp lệ: {value}")


def make_rejected_record(
    source_name,
    record_identifier,
    raw_data,
    reason,
):
    # Create one rejected-record entry for later auditing.
    return {
        "source_name": source_name,
        "record_identifier": str(record_identifier or ""),
        "raw_data": json.dumps(
            raw_data,
            ensure_ascii=False,
            default=str,
        ),
        "rejection_reason": reason,
    }


# TRANSFORM STUDENTS

def transform_students(students_df):
    valid_records = []
    rejected_records = []

    # Store the first valid record for each student_id.
    seen_students = {}

    for index, row in students_df.iterrows():
        raw = row.to_dict()

        student_id = clean_text(
            row.get("student_code", "")
        ).upper()

        try:
            # 1. Validate student code.
            if not student_id:
                raise ValueError("Thiếu mã sinh viên")

            if not STUDENT_CODE_PATTERN.fullmatch(student_id):
                raise ValueError(
                    f"Mã sinh viên không đúng định dạng: {student_id}"
                )

            # 2. Normalize and validate full name.
            full_name = clean_text(row.get("full_name", ""))

            if not full_name:
                raise ValueError("Thiếu họ tên sinh viên")

            # 3. Normalize and validate date of birth.
            dob = parse_date(row.get("date_of_birth", ""))

            if dob > date.today():
                raise ValueError("Ngày sinh nằm quá thời gian hiện tại")

            # 4. Normalize and validate class.
            class_name = clean_text(row.get("class", ""))

            if not class_name:
                raise ValueError("Thiếu thông tin lớp")

            # 5. Normalize optional email.
            email = clean_text(row.get("email", "")).lower()

            if email and not EMAIL_PATTERN.fullmatch(email):
                raise ValueError(f"Email không hợp lệ: {email}")

            record = {
                "student_id": student_id,
                "full_name": full_name,
                "date_of_birth": dob.isoformat(),
                "class_name": class_name,
                "email": email or None,
            }

            # 6. Detect duplicate student IDs.
            if student_id in seen_students:
                previous = seen_students[student_id]

                if previous == record:
                    reason = "Trùng lặp hoàn toàn với bản ghi trước đó"
                else:
                    reason = (
                        "Xung đột dữ liệu: trùng mã sinh viên "
                        "nhưng nội dung khác"
                    )

                rejected_records.append(
                    make_rejected_record(
                        "students",
                        student_id,
                        raw,
                        reason,
                    )
                )
                continue

            seen_students[student_id] = record
            valid_records.append(record)

        except ValueError as error:
            rejected_records.append(
                make_rejected_record(
                    "students",
                    student_id,
                    raw,
                    str(error),
                )
            )

    columns = [
        "student_id",
        "full_name",
        "date_of_birth",
        "class_name",
        "email",
    ]

    return (
        pd.DataFrame(valid_records, columns=columns),
        rejected_records,
    )


# TRANSFORM PAYMENTS

def transform_payments(payments_df, valid_student_ids):
    valid_records = []
    rejected_records = []

    # Store the first valid payment for each payment_id.
    seen_payments = {}

    for index, row in payments_df.iterrows():
        raw = row.to_dict()

        payment_id = clean_text(
            row.get("payment_id", "")
        ).upper()

        student_id = clean_text(
            row.get("student_code", "")
        ).upper()

        try:
            # 1. Validate payment ID.
            if not payment_id:
                raise ValueError("Thiếu mã giao dịch")

            # 2. Validate student code.
            if not student_id:
                raise ValueError("Thiếu mã sinh viên trong giao dịch")

            if not STUDENT_CODE_PATTERN.fullmatch(student_id):
                raise ValueError(
                    f"Mã sinh viên không đúng định dạng: {student_id}"
                )

            # 3. Convert amount to Decimal.
            amount_text = clean_text(row.get("amount", ""))

            try:
                amount = Decimal(amount_text)
            except InvalidOperation:
                raise ValueError(
                    f"Số tiền không hợp lệ: {amount_text}"
                )

            if not amount.is_finite():
                raise ValueError("Số tiền không phải giá trị hữu hạn")

            if amount <= 0:
                raise ValueError("Số tiền phải lớn hơn 0")

            if amount.as_tuple().exponent < -2:
                raise ValueError(
                    "Số tiền không được có quá 2 chữ số thập phân"
                )

            amount = amount.quantize(Decimal("0.01"))

            # 4. Normalize payment date.
            payment_date = parse_payment_datetime(
                row.get("payment_date", "")
            )

            # 5. Normalize payment status.
            status = clean_text(
                row.get("status", "")
            ).upper()

            if status not in ALLOWED_PAYMENT_STATUSES:
                raise ValueError(
                    f"Trạng thái thanh toán không hợp lệ: {status}"
                )

            # 6. Check student existence.
            if student_id not in valid_student_ids:
                raise ValueError(
                    f"Không tìm thấy sinh viên {student_id} "
                    "trong dữ liệu sinh viên hợp lệ"
                )

            record = {
                "payment_id": payment_id,
                "student_id": student_id,
                "amount": str(amount),
                "payment_date": payment_date.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "status": status,
            }

            # 7. Detect duplicate payment IDs.
            if payment_id in seen_payments:
                previous = seen_payments[payment_id]

                if previous == record:
                    reason = "Trùng giao dịch hoàn toàn với bản ghi trước đó"
                else:
                    reason = (
                        "Xung đột giao dịch: trùng payment_id "
                        "nhưng nội dung khác"
                    )

                rejected_records.append(
                    make_rejected_record(
                        "payments",
                        payment_id,
                        raw,
                        reason,
                    )
                )
                continue

            seen_payments[payment_id] = record
            valid_records.append(record)

        except ValueError as error:
            rejected_records.append(
                make_rejected_record(
                    "payments",
                    payment_id,
                    raw,
                    str(error),
                )
            )

    columns = [
        "payment_id",
        "student_id",
        "amount",
        "payment_date",
        "status",
    ]

    return (
        pd.DataFrame(valid_records, columns=columns),
        rejected_records,
    )


# MAIN TRANSFORM PIPELINE


def transform_data(run_id):
    run_extracted_dir = EXTRACTED_DIR / run_id
    run_transformed_dir = TRANSFORMED_DIR / run_id

    students_file = run_extracted_dir / "students_extracted.csv"
    payments_file = run_extracted_dir / "payments_extracted.csv"

    if not students_file.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file: {students_file}"
        )

    if not payments_file.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file: {payments_file}"
        )

    run_transformed_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Read extracted snapshots.
    students_df = pd.read_csv(
        students_file,
        dtype=str,
        keep_default_na=False,
    )

    payments_df = pd.read_csv(
        payments_file,
        dtype=str,
        keep_default_na=False,
    )

    # Transform students first.
    students_valid, students_rejected = transform_students(
        students_df
    )

    # Only valid students can be referenced by payments.
    valid_student_ids = set(
        students_valid["student_id"].tolist()
    )

    # Transform payments using valid student IDs.
    payments_valid, payments_rejected = transform_payments(
        payments_df,
        valid_student_ids,
    )

    all_rejected = students_rejected + payments_rejected

    # Save transformed outputs.
    students_valid.to_csv(
        run_transformed_dir / "students_transformed.csv",
        index=False,
        encoding="utf-8-sig",
    )

    payments_valid.to_csv(
        run_transformed_dir / "payments_transformed.csv",
        index=False,
        encoding="utf-8-sig",
    )

    pd.DataFrame(
        all_rejected,
        columns=[
            "source_name",
            "record_identifier",
            "raw_data",
            "rejection_reason",
        ],
    ).to_csv(
        run_transformed_dir / "rejected_records.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # Print summary.
    print("\n" + "=" * 50)
    print("TRANSFORM RESULT")
    print("=" * 50)

    print(f"Run ID: {run_id}")

    print("\nSTUDENTS")
    print(f"Input: {len(students_df)}")
    print(f"Valid: {len(students_valid)}")
    print(f"Rejected / Duplicate: {len(students_rejected)}")

    print("\nPAYMENTS")
    print(f"Input: {len(payments_df)}")
    print(f"Valid: {len(payments_valid)}")
    print(f"Rejected / Duplicate: {len(payments_rejected)}")

    print("\nTOTAL")
    print(f"Input: {len(students_df) + len(payments_df)}")
    print(f"Valid: {len(students_valid) + len(payments_valid)}")
    print(f"Rejected: {len(all_rejected)}")

    print("\nTRANSFORMED FILES:")
    print(run_transformed_dir)

    return {
        "students": students_valid,
        "payments": payments_valid,
        "rejected": all_rejected,
    }


# STANDALONE TEST

if __name__ == "__main__":
    run_id = "20261125_212011"
    transform_data(run_id)
