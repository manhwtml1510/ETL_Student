# ETL Student Project

Dự án ETL (Extract - Transform - Load) tích hợp dữ liệu sinh viên từ CSV và dữ liệu thanh toán từ MySQL vào data warehouse MySQL.

## Tính năng

- Đọc dữ liệu sinh viên từ `data/source/students.csv`.
- Trích xuất bảng `raw_payments` từ database nguồn `payment_source`.
- Chuẩn hóa và kiểm tra dữ liệu sinh viên, thanh toán.
- Loại bỏ bản ghi trùng lặp và ghi lý do từ chối.
- Nạp dữ liệu vào database đích `student_warehouse` theo cơ chế:
  - **Insert** khi bản ghi chưa tồn tại.
  - **Update** khi sinh viên đã tồn tại nhưng thông tin thay đổi.
  - **Skip** khi dữ liệu trùng hoàn toàn.
- Ghi log chạy ETL, bản ghi bị loại và kết quả kiểm tra chất lượng.
- Đảm bảo toàn bộ transaction Load được rollback nếu phát sinh lỗi.

## Công nghệ

- Python 3
- pandas
- SQLAlchemy
- PyMySQL
- python-dotenv
- MySQL

## Cấu trúc thư mục

```text
ETL_Student_Project/
├── main.py                         # Điểm chạy chính của pipeline
├── config.py                       # Cấu hình kết nối database
├── generate_source_data.py         # Tạo CSV sinh viên và SQL thanh toán mẫu
├── check_source_data.py            # Kiểm tra nhanh dữ liệu sinh viên
├── requirements.txt
├── .env                            # Cấu hình kết nối (tạo từ mẫu bên dưới)
├── database/
│   ├── create_payment_source.sql   # Tạo database thanh toán
│   ├── seed_payment_source.sql     # Dữ liệu thanh toán mẫu
│   └── warehouse_schema.sql        # Tạo schema data warehouse
├── etl/
│   ├── extract.py                  # Extract CSV và MySQL
│   ├── transform.py                # Chuẩn hóa, validate và deduplicate
│   └── load.py                     # Insert/update/skip và transaction
├── data/
│   ├── source/                     # Dữ liệu sinh viên đầu vào
│   ├── extracted/<run_id>/         # Snapshot sau Extract
│   ├── transformed/<run_id>/       # Dữ liệu sau Transform
│   └── rejected/                   # Thư mục dự trữ cho dữ liệu loại
├── logs/
├── reports/
└── test_*.py                       # Các kịch bản kiểm thử Load
```

## Cài đặt

### 1. Tạo môi trường Python

```powershell
cd D:\ETL_Student_Project
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Cấu hình MySQL

Cài đặt MySQL và đảm bảo MySQL Server đang chạy. Tài khoản cấu hình phải có quyền tạo database và thao tác trên `payment_source`, `student_warehouse`.

### 3. Tạo file `.env`

Tạo file `.env` tại thư mục gốc dự án với nội dung sau:

```dotenv
SOURCE_DB_HOST=localhost
SOURCE_DB_PORT=3306
SOURCE_DB_NAME=payment_source
SOURCE_DB_USER=your_mysql_user
SOURCE_DB_PASSWORD=your_mysql_password

TARGET_DB_HOST=localhost
TARGET_DB_PORT=3306
TARGET_DB_NAME=student_warehouse
TARGET_DB_USER=your_mysql_user
TARGET_DB_PASSWORD=your_mysql_password
```

Không commit `.env` hoặc thông tin đăng nhập MySQL lên Git.

### 4. Khởi tạo database

Chạy các script bằng MySQL CLI hoặc MySQL Workbench:

```powershell
mysql -u root -p < database/create_payment_source.sql
mysql -u root -p < database/seed_payment_source.sql
mysql -u root -p < database/warehouse_schema.sql
```

Nếu cần tạo lại dữ liệu sinh viên và sinh file seed thanh toán:

```powershell
python generate_source_data.py
```

Sau đó chạy lại `seed_payment_source.sql` nếu bảng thanh toán nguồn chưa chứa dữ liệu mong muốn.

## Chạy ETL

```powershell
python main.py
```

Mỗi lần chạy pipeline tạo một `run_id` theo định dạng `YYYYMMDD_HHMMSS`.

Kết quả:

- Snapshot Extract: `data/extracted/<run_id>/`
- Snapshot Transform: `data/transformed/<run_id>/`
- Chạy và thống kê được lưu trong bảng `etl_runs`.
- Bản ghi bị loại được lưu trong `rejected_records`.
- Kết quả data quality được lưu trong `data_quality_results`.

## Quy tắc xử lý dữ liệu

### Sinh viên

- Mã sinh viên bắt buộc có định dạng `SV` + 3 chữ số, ví dụ `SV001`.
- Họ tên và lớp không được để trống.
- Ngày sinh hỗ trợ `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY` hoặc `YYYY/MM/DD`.
- Ngày sinh không được nằm trong tương lai.
- Email hợp lệ là tùy chọn.
- Hai bản ghi có cùng mã sinh viên:
  - Nội dung giống nhau: xem là bản ghi trùng.
  - Nội dung khác nhau: xem là xung đột dữ liệu.

### Thanh toán

- `payment_id` không được để trống.
- `student_code` phải tồn tại trong tập sinh viên hợp lệ.
- Số tiền phải hữu hạn, lớn hơn 0 và tối đa 2 chữ số thập phân.
- Ngày thanh toán hỗ trợ định dạng ngày và `datetime`.
- Trạng thái hợp lệ: `PAID`, `PENDING`, `FAILED`.
- Hai giao dịch có cùng `payment_id`:
  - Nội dung giống nhau: xem là bản ghi trùng.
  - Nội dung khác nhau: xem là xung đột dữ liệu.

## Kiểm tra

Kiểm tra dữ liệu CSV mẫu:

```powershell
python check_source_data.py
```

Các kịch bản load cần chạy sau ít nhất một lần `python main.py` để có thư mục Transform mới nhất:

```powershell
# Kiểm thử cập nhật sinh viên
python test_update.py

# Kiểm thử phát hiện xung đột payment_id
python test_payment_conflict.py

# Kiểm thử rollback toàn bộ transaction
python test_rollback.py
```

Các script kiểm thử tự khôi phục file Transform đã thay đổi tạm thời.

## Trạng thái ETL

- `RUNNING`: đang chạy và đã tạo bản ghi cho lần chạy.
- `SUCCESS`: load thành công, không có bản ghi bị loại hoặc xung đột.
- `PARTIAL`: load thành công nhưng có bản ghi bị loại/xung đột.
- `FAILED`: transaction Load thất bại và đã rollback.
