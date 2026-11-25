CREATE DATABASE IF NOT EXISTS payment_source
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE payment_source;

CREATE TABLE IF NOT EXISTS raw_payments (
    source_row_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    payment_id VARCHAR(30),
    student_code VARCHAR(30),
    amount VARCHAR(50),
    payment_date VARCHAR(50),
    status VARCHAR(30),

    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_payment_id (payment_id),
    INDEX idx_student_code (student_code)
) ENGINE=InnoDB;
