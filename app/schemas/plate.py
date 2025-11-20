from pydantic import BaseModel
from datetime import datetime

class PlateBase(BaseModel):
    plate_text: str
    province: str | None = None
    vehicle_type: str | None = None
    owner_name: str | None = None
    is_blacklisted: bool = False
    blacklist_reason: str | None = None

class PlateCreate(PlateBase):
    pass

class PlateUpdate(BaseModel):
    province: str | None = None
    vehicle_type: str | None = None
    owner_name: str | None = None
    is_blacklisted: bool | None = None
    blacklist_reason: str | None = None

class PlateOut(PlateBase):
    id: int
    created_at: datetime
    detection_count: int = 0  # Số lần detect
    last_seen: datetime | None = None  # Lần detect cuối
    class Config:
        from_attributes = True
