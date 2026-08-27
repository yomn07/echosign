import os
from pathlib import Path

from dotenv import load_dotenv
from jose import jwt, JWTError

load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


def get_user_from_token(token: str | None):

    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            return None

        return {
            "id": user_id,
            "email": email,
        }

    except JWTError:
        return None