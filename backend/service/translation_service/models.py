from sqlalchemy import Column, String, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from database import Base

class Landmark(Base):
    __tablename__ = "landmarks"

    id = Column(
        BigInteger,
        primary_key=True,
        index=True
    )

    text = Column(
        String,
        nullable=False,
        index=True
    )

    landmarks = Column(
        JSONB,
        nullable=False
    )