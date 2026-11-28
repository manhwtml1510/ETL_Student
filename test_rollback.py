
import pandas as pd

from config import BASE_DIR
from etl.load import load_data

TRANSFORMED_DIR = BASE_DIR / "data" / "transformed"

# Lấy thư mục Transform mới nhất
run_dirs = sorted(
    [path for path in TRANSFORMED_DIR.iterdir() if path.is_dir()],
    key=lambda path: path.name
)

if not run_dirs:
    raise FileNotFoundError("Không tìm thấy thư mục Transformed")

run_dir = run_dirs[-1]
run_id = run_dir.name

students_file = run_dir / "students_transformed.csv"
payments_file = run_dir / "payments_transformed.csv"

if not students_file.exists() or not payments_file.exists():
    raise FileNotFoundError("Thiếu file Transform cần thiết")

# Sao lưu nội dung gốc của cả hai file
original_students = students_file.read_bytes()
original_payments = payments_file.read_bytes()

try:
    students_df = pd.read_csv(
        students_file,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig"
    )

    payments_df = pd.read_csv(
        payments_file,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig"
    )

    # 1. Tạo thay đổi hợp lệ để kiểm tra UPDATE có bị rollback không
    student_mask = students_df["student_id"] == "SV001"

    if not student_mask.any():
        raise ValueError("Không tìm thấy SV001")

    original_class = students_df.loc[
        student_mask, "class_name"
    ].iloc[0]

    students_df.loc[
        student_mask, "class_name"
    ] = "ROLLBACK_TEST"

    # 2. Thêm giao dịch có khóa ngoại không hợp lệ
    if (payments_df["payment_id"] == "PAY_ROLLBACK_TEST").any():
        raise ValueError("PAY_ROLLBACK_TEST đã tồn tại trong file")

    test_payment = {
        "payment_id": "PAY_ROLLBACK_TEST",
        "student_id": "SV999",
        "amount": "1.00",
        "payment_date": "2026-11-28 08:00:00",
        "status": "PENDING"
    }

    payments_df = pd.concat(
        [payments_df, pd.DataFrame([test_payment])],
        ignore_index=True
    )

    # Ghi dữ liệu kiểm thử tạm thời
    students_df.to_csv(
        students_file,
        index=False,
        encoding="utf-8-sig"
    )

    payments_df.to_csv(
        payments_file,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Run ID: {run_id}")
    print(f"SV001 class ban đầu: {original_class}")
    print("SV001 class kiểm thử: ROLLBACK_TEST")
    print("Giao dịch lỗi: PAY_ROLLBACK_TEST")
    print("Student ID không tồn tại: SV999")

    print("\n[1] BẮT ĐẦU KIỂM THỬ TRANSACTION ROLLBACK")

    try:
        result = load_data(run_id)
        print("Load trả về:", result)
    except Exception as error:
        print("\nĐã phát sinh lỗi như dự kiến:")
        print(type(error).__name__, error)

finally:
    # Luôn khôi phục file Transform ban đầu
    students_file.write_bytes(original_students)
    payments_file.write_bytes(original_payments)

    print("\n[2] ĐÃ KHÔI PHỤC FILE TRANSFORM GỐC")

print("\nHOÀN TẤT KIỂM THỬ")
