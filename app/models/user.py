# models/user.py
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, func
from ..core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), nullable=False)  # admin, staff
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())