import os
from pathlib import Path

from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

# ============================================================
# DATABASE CONFIGURATION
# ============================================================

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")


# ============================================================
# VALIDATE CONFIGURATION
# ============================================================

if not POSTGRES_USER:
    raise RuntimeError("POSTGRES_USER is not configured")

if not POSTGRES_PASSWORD:
    raise RuntimeError("POSTGRES_PASSWORD is not configured")

if not POSTGRES_DB:
    raise RuntimeError("POSTGRES_DB is not configured")

if not POSTGRES_HOST:
    raise RuntimeError("POSTGRES_HOST is not configured")

if not POSTGRES_PORT:
    raise RuntimeError("POSTGRES_PORT is not configured")


# ============================================================
# DATABASE URL
# ============================================================

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)


# ============================================================
# SQLALCHEMY
# ============================================================

engine = create_engine(
    DATABASE_URL
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


Base = declarative_base()


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()