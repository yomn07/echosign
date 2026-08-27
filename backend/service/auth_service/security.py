import os
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from jose import jwt

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


SECRET_KEY = os.getenv("SECRET_KEY")

ALGORITHM = os.getenv(
    "ALGORITHM",
    "HS256"
)


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=60
    )

    to_encode.update({
        "exp": expire
    })

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def create_email_verification_token(email: str):

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=30
    )

    data = {
        "sub": email,
        "purpose": "email_verification",
        "exp": expire
    }

    return jwt.encode(
        data,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def verify_email_verification_token(token: str):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        if payload.get("purpose") != "email_verification":
            return None

        email = payload.get("sub")

        if not email:
            return None

        return email

    except Exception:
        return None