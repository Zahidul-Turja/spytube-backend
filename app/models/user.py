from sqlalchemy import Column, Integer, String, JSON
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    picture = Column(String, nullable=True)
    google_id = Column(String, nullable=True)
    tokens = Column(JSON, nullable=True)

    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
