# models/detection.py
from sqlalchemy import Column, BigInteger, Integer, Float, TIMESTAMP, String, Text, Boolean, ForeignKey, func
from ..core.database import Base

class Detection(Base):
    __tablename__ = "detections"

    id = Column(BigInteger, primary_key=True, index=True)
    plate_id = Column(Integer, ForeignKey("plates.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    confidence = Column(Float, nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.now(), index=True)
    raw_text = Column(String(50))
    crop_image_path = Column(Text)
    is_verified = Column(Boolean, default=False)