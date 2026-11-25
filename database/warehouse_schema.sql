CREATE DATABASE IF NOT EXISTS student_warehouse
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE student_warehouse;

-- 1. Bang sinh vien
CREATE TABLE IF NOT EXISTS students (
    student_id VARCHAR(20) PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    date_of_birth DATE NOT NULL,
    class_name VARCHAR(50) NOT NULL,
    email VARCHAR(150),

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Bang giao dich thanh toan
CREATE TABLE IF NOT EXISTS payments (
    payment_id VARCHAR(30) PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    payment_date DATETIME NOT NULL,
    status VARCHAR(20) NOT NULL,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_payments_students
        FOREIGN KEY (student_id)
        REFERENCES students(student_id),

    CONSTRAINT chk_payment_amount
        CHECK (amount > 0),

    INDEX idx_payments_student_id (student_id),
    INDEX idx_payments_payment_date (payment_date)
) ENGINE=InnoDB;

-- 3. Bang quan ly cac lan chay ETL
CREATE TABLE IF NOT EXISTS etl_runs (
    run_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'RUNNING',

    extracted_count INT NOT NULL DEFAULT 0,
    transformed_count INT NOT NULL DEFAULT 0,
    rejected_count INT NOT NULL DEFAULT 0,
    inserted_count INT NOT NULL DEFAULT 0,
    updated_count INT NOT NULL DEFAULT 0,
    skipped_count INT NOT NULL DEFAULT 0,

    INDEX idx_etl_runs_started_at (started_at)
) ENGINE=InnoDB;

-- 4. Bang luu ban ghi bi loai
CREATE TABLE IF NOT EXISTS rejected_records (
    reject_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    run_id BIGINT NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    record_identifier VARCHAR(100),
    raw_data JSON NOT NULL,
    rejection_reason VARCHAR(255) NOT NULL,
    rejected_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_rejected_etl_runs
        FOREIGN KEY (run_id)
        REFERENCES etl_runs(run_id),

    INDEX idx_rejected_run_id (run_id)
) ENGINE=InnoDB;

-- 5. Bang ket qua kiem tra chat luong
CREATE TABLE IF NOT EXISTS data_quality_results (
    result_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    run_id BIGINT NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    rule_name VARCHAR(100) NOT NULL,
    total_checked INT NOT NULL DEFAULT 0,
    passed_count INT NOT NULL DEFAULT 0,
    failed_count INT NOT NULL DEFAULT 0,
    checked_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_quality_etl_runs
        FOREIGN KEY (run_id)
        REFERENCES etl_runs(run_id),

    INDEX idx_quality_run_id (run_id)
) ENGINE=InnoDB;
