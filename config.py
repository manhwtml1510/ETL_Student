import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, URL


# Thu muc goc cua du an
BASE_DIR = Path(__file__).resolve().parent

# Doc thong tin tu file .env
load_dotenv(BASE_DIR / ".env")


def create_source_engine():

    # Tao ket noi toi database nguon payment_source.

    url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("SOURCE_DB_USER"),
        password=os.getenv("SOURCE_DB_PASSWORD"),
        host=os.getenv("SOURCE_DB_HOST", "localhost"),
        port=int(os.getenv("SOURCE_DB_PORT", "3306")),
        database=os.getenv("SOURCE_DB_NAME", "payment_source"),
        query={"charset": "utf8mb4"}
    )

    engine = create_engine(
        url,
        pool_pre_ping=True
    )

    return engine


def create_target_engine():
    
    # Tao ket noi toi database dich student_warehouse.

    url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("TARGET_DB_USER"),
        password=os.getenv("TARGET_DB_PASSWORD"),
        host=os.getenv("TARGET_DB_HOST", "localhost"),
        port=int(os.getenv("TARGET_DB_PORT", "3306")),
        database=os.getenv("TARGET_DB_NAME", "student_warehouse"),
        query={"charset": "utf8mb4"}
    )

    engine = create_engine(
        url,
        pool_pre_ping=True
    )

    return engine
