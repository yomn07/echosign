import os

from dotenv import load_dotenv


load_dotenv()


# ============================================================
# SERVICE
# ============================================================

SERVICE_NAME = "auth-service"

HOST = os.getenv(
    "AUTH_SERVICE_HOST",
    "0.0.0.0",
)

PORT = int(
    os.getenv(
        "AUTH_SERVICE_PORT",
        "8000",
    )
)


# ============================================================
# DATABASE
# ============================================================

POSTGRES_USER = os.getenv(
    "POSTGRES_USER",
)

POSTGRES_PASSWORD = os.getenv(
    "POSTGRES_PASSWORD",
)

POSTGRES_DB = os.getenv(
    "POSTGRES_DB",
)

POSTGRES_HOST = os.getenv(
    "POSTGRES_HOST",
    "localhost",
)

POSTGRES_PORT = os.getenv(
    "POSTGRES_PORT",
    "5433",
)


DATABASE_URL = (
    f"postgresql://"
    f"{POSTGRES_USER}:"
    f"{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:"
    f"{POSTGRES_PORT}/"
    f"{POSTGRES_DB}"
)


# ============================================================
# JWT
# ============================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
)

ALGORITHM = os.getenv(
    "ALGORITHM",
    "HS256",
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "60",
    )
)


# ============================================================
# FRONTEND
# ============================================================

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:8080",
)