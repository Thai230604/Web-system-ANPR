# models/plate.py
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Text, func
from ..core.database import Base

class Plate(Base):
    __tablename__ = "plates"

    id = Column(Integer, primary_key=True, index=True)
    plate_text = Column(String(20), unique=True, nullable=False, index=True)
    province = Column(String(50))
    vehicle_type = Column(String(30))
    owner_name = Column(String(100))
    is_blacklisted = Column(Boolean, default=False)
    blacklist_reason = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())