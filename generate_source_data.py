
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / "data" / "source"

SOURCE_DIR.mkdir(parents=True, exist_ok=True)

# Du lieu sinh vien hop le
first_names = [
    "Nguyen Van", "Tran Thi", "Le Van", "Pham Thi",
    "Hoang Van", "Do Thi", "Bui Van", "Vu Thi",
    "Dang Van", "Ngo Thi"
]

last_names = [
    "An", "Binh", "Cuong", "Dung", "Hanh",
    "Hoa", "Linh", "Minh", "Nam", "Trang"
]

students = []

for i in range(1, 41):
    student_id = f"SV{i:03d}"
    full_name = f"{first_names[(i-1) % 10]} {last_names[(i-1) % 10]}"
    day = (i % 27) + 1
    month = (i % 12) + 1
    year = 2005 if i % 2 == 0 else 2006

    students.append({
        "student_code": student_id,
        "full_name": full_name,
        "date_of_birth": f"{year}-{month:02d}-{day:02d}",
        "class": f"CNTT{(i % 3) + 1:02d}",
        "email": f"sv{i:03d}@example.com"
    })

# 8 ban ghi sai du lieu
invalid_students = [
    {
        "student_code": "",
        "full_name": "Nguyen Van A",
        "date_of_birth": "2006-01-15",
        "class": "CNTT01",
        "email": "a@example.com"
    },
    {
        "student_code": "SV042",
        "full_name": "",
        "date_of_birth": "2006-02-15",
        "class": "CNTT01",
        "email": "b@example.com"
    },
    {
        "student_code": "SV043",
        "full_name": "Le Van C",
        "date_of_birth": "31/02/2006",
        "class": "CNTT02",
        "email": "c@example.com"
    },
    {
        "student_code": "SV044",
        "full_name": "Pham Thi D",
        "date_of_birth": "not-a-date",
        "class": "CNTT02",
        "email": "d@example.com"
    },
    {
        "student_code": "SV045",
        "full_name": "Hoang Van E",
        "date_of_birth": "2006-05-20",
        "class": "",
        "email": "e@example.com"
    },
    {
        "student_code": "SV046",
        "full_name": "Do Thi F",
        "date_of_birth": "",
        "class": "CNTT03",
        "email": "f@example.com"
    },
    {
        "student_code": "SV047",
        "full_name": "Bui Van G",
        "date_of_birth": "2035-01-01",
        "class": "CNTT01",
        "email": "g@example.com"
    },
    {
        "student_code": "SV048",
        "full_name": "Vu Thi H",
        "date_of_birth": "2006/99/99",
        "class": "CNTT02",
        "email": "h@example.com"
    }
]

# 8 ban ghi trung lap hoan toan voi 8 sinh vien dau tien
duplicate_students = [
    row.copy() for row in students[:8]
]

# 4 ban ghi hop le nhung can chuan hoa
normalization_students = [
    {
        "student_code": "sv049",
        "full_name": "  Nguyen Van K  ",
        "date_of_birth": "15/10/2006",
        "class": "CNTT01",
        "email": "k@example.com"
    },
    {
        "student_code": " SV050 ",
        "full_name": "Tran Thi L",
        "date_of_birth": "20/05/2006",
        "class": "CNTT02",
        "email": "l@example.com"
    },
    {
        "student_code": "sv051",
        "full_name": "Le Van M ",
        "date_of_birth": "2005-12-20",
        "class": "CNTT03",
        "email": "m@example.com"
    },
    {
        "student_code": " SV052 ",
        "full_name": "Pham Thi N",
        "date_of_birth": "01/08/2006",
        "class": "CNTT01",
        "email": "n@example.com"
    }
]

all_students = (
    students
    + invalid_students
    + duplicate_students
    + normalization_students
)

output_file = SOURCE_DIR / "students.csv"

with open(output_file, "w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "student_code",
            "full_name",
            "date_of_birth",
            "class",
            "email"
        ]
    )

    writer.writeheader()
    writer.writerows(all_students)

print("Tao du lieu CSV thanh cong!")
print(f"Tong so ban ghi: {len(all_students)}")
print(f"Du lieu hop le thong thuong: {len(students)}")
print(f"Du lieu sai: {len(invalid_students)}")
print(f"Du lieu trung lap: {len(duplicate_students)}")
print(f"Du lieu can chuan hoa: {len(normalization_students)}")
print(f"File: {output_file}")


# TAO DU LIEU THANH TOAN CHO MYSQL


valid_student_ids = (
    [f"SV{i:03d}" for i in range(1, 41)]
    + ["SV049", "SV050", "SV051", "SV052"]
)

payments = []

# 45 giao dich hop le
for i in range(1, 46):
    student_id = valid_student_ids[(i - 1) % len(valid_student_ids)]

    payments.append({
        "payment_id": f"PAY{i:03d}",
        "student_code": student_id,
        "amount": str(1000000 + i * 100000),
        "payment_date": f"2026-10-{(i % 28) + 1:02d} 09:00:00",
        "status": "PAID"
    })

# 5 giao dich trung ma, trung noi dung
duplicate_payments = [
    row.copy() for row in payments[:5]
]

# 5 giao dich sai so tien hoac ngay
invalid_payments = [
    {
        "payment_id": "PAY051",
        "student_code": "SV001",
        "amount": "abc",
        "payment_date": "2026-10-10 09:00:00",
        "status": "PAID"
    },
    {
        "payment_id": "PAY052",
        "student_code": "SV002",
        "amount": "-500000",
        "payment_date": "2026-10-11 09:00:00",
        "status": "PAID"
    },
    {
        "payment_id": "PAY053",
        "student_code": "SV003",
        "amount": "0",
        "payment_date": "2026-10-12 09:00:00",
        "status": "PAID"
    },
    {
        "payment_id": "PAY054",
        "student_code": "SV004",
        "amount": "2000000",
        "payment_date": "31/02/2026",
        "status": "PAID"
    },
    {
        "payment_id": "PAY055",
        "student_code": "SV005",
        "amount": "3000000",
        "payment_date": "not-a-date",
        "status": "PAID"
    }
]

# 5 giao dich tham chieu sinh vien khong ton tai
orphan_payments = []

for i in range(56, 61):
    orphan_payments.append({
        "payment_id": f"PAY{i:03d}",
        "student_code": f"SV{900 + i:03d}",
        "amount": "2000000",
        "payment_date": "2026-10-15 09:00:00",
        "status": "PAID"
    })

all_payments = (
    payments
    + duplicate_payments
    + invalid_payments
    + orphan_payments
)

# Tao file SQL insert du lieu
def sql_value(value):
    return "'" + str(value).replace("\\", "\\\\").replace("'", "''") + "'"

sql_lines = [
    "USE payment_source;",
    "",
    "INSERT INTO raw_payments",
    "(payment_id, student_code, amount, payment_date, status)",
    "VALUES"
]

value_lines = []

for row in all_payments:
    values = [
        sql_value(row["payment_id"]),
        sql_value(row["student_code"]),
        sql_value(row["amount"]),
        sql_value(row["payment_date"]),
        sql_value(row["status"])
    ]

    value_lines.append("(" + ", ".join(values) + ")")

sql_lines.append(",\n".join(value_lines) + ";")

seed_file = BASE_DIR / "database" / "seed_payment_source.sql"
seed_file.parent.mkdir(parents=True, exist_ok=True)
seed_file.write_text("\n".join(sql_lines), encoding="utf-8")

print("\nDU LIEU THANH TOAN:")
print(f"Tong giao dich: {len(all_payments)}")
print(f"Giao dich hop le: {len(payments)}")
print(f"Giao dich trung: {len(duplicate_payments)}")
print(f"Giao dich sai: {len(invalid_payments)}")
print(f"Giao dich sai ma sinh vien: {len(orphan_payments)}")
print(f"File SQL: {seed_file}")
