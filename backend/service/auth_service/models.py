from sqlalchemy import Column, Integer, String, DateTime, Boolean ,BigInteger
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

    email = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    hashed_password = Column(String, nullable=False)

    role = Column(String, nullable=True)

    # Email verification
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False
    )


    verification_token = Column(
        String,
        nullable=True
    )

    verification_expires_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    # Password reset
    reset_token_hash = Column(
        String,
        nullable=True
    )

    reset_token_expires = Column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
