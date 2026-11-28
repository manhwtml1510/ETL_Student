
from decimal import Decimal
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

payments_file = run_dir / "payments_transformed.csv"

if not payments_file.exists():
    raise FileNotFoundError(f"Không tìm thấy file: {payments_file}")

# Sao lưu nguyên trạng file để khôi phục chính xác
original_content = payments_file.read_bytes()
first_error = None

try:
    payments_df = pd.read_csv(
        payments_file,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig"
    )

    mask = payments_df["payment_id"] == "PAY001"

    if not mask.any():
        raise ValueError("Không tìm thấy PAY001 trong file Transform")

    original_amount = Decimal(
        payments_df.loc[mask, "amount"].iloc[0]
    )

    modified_amount = original_amount + Decimal("1.00")

    payments_df.loc[mask, "amount"] = f"{modified_amount:.2f}"

    payments_df.to_csv(
        payments_file,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Run ID: {run_id}")
    print(f"PAY001 amount ban đầu: {original_amount}")
    print(f"PAY001 amount kiểm thử: {modified_amount}")

    print("\n[1] LOAD DỮ LIỆU ĐÃ THAY ĐỔI")
    first_result = load_data(run_id)

except Exception as error:
    first_error = error

finally:
    # Luôn khôi phục file Transform về nội dung ban đầu
    payments_file.write_bytes(original_content)

print("\n[2] LOAD LẠI DỮ LIỆU GỐC")
restore_result = load_data(run_id)

if first_error is not None:
    raise first_error

print("\nKIỂM THỬ PAYMENT CONFLICT HOÀN TẤT")
