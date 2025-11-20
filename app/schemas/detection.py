# schemas/detection.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class DetectionBase(BaseModel):
    plate_text: str = Field(..., min_length=1, max_length=50)
    confidence: float = Field(..., ge=0.0, le=1.0)
    raw_text: Optional[str] = None
    crop_image_path: Optional[str] = None

class DetectionCreate(DetectionBase):
    """Schema để tạo detection mới"""
    tracker_id: Optional[int] = None  # ByteTrack ID
    bbox: Optional[list[int]] = None  # [x1, y1, x2, y2]

class DetectionResponse(DetectionBase):
    id: int
    plate_id: int
    user_id: Optional[int]
    timestamp: datetime
    is_verified: bool
    
    # Thông tin từ Plate (joined)
    plate_province: Optional[str] = None
    plate_owner: Optional[str] = None
    is_blacklisted: bool = False
    blacklist_reason: Optional[str] = None
    
    class Config:
        from_attributes = True

class DetectionStats(BaseModel):
    """Thống kê detection"""
    total_detections: int
    verified_detections: int
    blacklisted_detections: int
    unique_plates: int
    today_detections: int