# services/detection_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from app.models.detection import Detection
from app.models.plate import Plate
from app.schemas.detection import DetectionCreate, DetectionResponse
from app.utils.format_plate import standardize_plate
from app.utils import validate_plate
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import threading
import time

class DetectionTracker:
    """
    Singleton class để track detections và tránh spam DB
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Track lần lưu cuối của mỗi tracker_id
        self.last_saved: Dict[int, datetime] = {}
        self.cooldown_seconds = 10  # Chỉ lưu 1 lần mỗi 10s cho mỗi xe
        self._initialized = True
        
        # Cleanup thread để xóa old entries
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
    
    def should_save(self, tracker_id: int) -> bool:
        """
        Kiểm tra có nên lưu detection này không
        """
        if tracker_id is None:
            return True  # Không có tracker_id → luôn lưu
        
        now = datetime.now()
        
        with self._lock:
            # Kiểm tra lần lưu cuối
            if tracker_id in self.last_saved:
                last_time = self.last_saved[tracker_id]
                time_diff = (now - last_time).total_seconds()
                
                if time_diff < self.cooldown_seconds:
                    return False  # Còn trong cooldown → không lưu
            
            # Update last saved time
            self.last_saved[tracker_id] = now
            return True
    
    def _cleanup_worker(self):
        """
        Background thread để xóa old tracker entries (sau 60s không thấy)
        """
        while self.running:
            time.sleep(30)  # Chạy mỗi 30s
            
            now = datetime.now()
            with self._lock:
                # Xóa entries cũ hơn 60s
                self.last_saved = {
                    tid: ts for tid, ts in self.last_saved.items()
                    if (now - ts).total_seconds() < 60
                }

# Global tracker instance
detection_tracker = DetectionTracker()

class DetectionService:
    """
    Service để quản lý detections
    """
    
    @staticmethod
    def get_or_create_plate(db: Session, plate_text: str) -> Plate:
        """
        Lấy hoặc tạo mới plate trong DB
        Tự động chuẩn hóa plate_text sang dạng chuẩn
        Validate format trước khi lưu
        """
        # Normalize plate text (chuẩn hóa sang dạng chuẩn)
        plate_text = standardize_plate(plate_text)
        
        # Validate plate format
        validation_result = validate_plate(plate_text)
        if not validation_result['valid']:
            print(f"[WARNING] Invalid plate format: {plate_text} - {validation_result['error']}")
            # Vẫn lưu nhưng ghi log, vì đây là OCR output nên có thể không hoàn hảo
            # Nếu muốn strict reject, bỏ comment ở dưới:
            # raise ValueError(f"Invalid plate format: {validation_result['error']}")
        
        # Tìm plate trong DB
        plate = db.query(Plate).filter(Plate.plate_text == plate_text).first()
        
        if plate:
            return plate
        
        # Tạo mới nếu chưa có
        new_plate = Plate(
            plate_text=plate_text,
            province=None,  # Có thể parse từ plate_text sau
            vehicle_type=None,
            owner_name=None
        )
        db.add(new_plate)
        db.commit()
        db.refresh(new_plate)
        
        return new_plate
    
    @staticmethod
    def create_detection(
        db: Session,
        detection_data: DetectionCreate,
        user_id: Optional[int] = None,
        tracker_id: Optional[int] = None
    ) -> Optional[Detection]:
        """
        Tạo detection mới với anti-spam logic
        
        Returns:
            Detection object nếu được lưu, None nếu skip do cooldown
        """
        # ✅ ANTI-SPAM: Kiểm tra cooldown
        if tracker_id is not None and not detection_tracker.should_save(tracker_id):
            print(f"[DETECTION] Skip saving tracker_id={tracker_id} (cooldown)")
            return None
        
        # Lấy hoặc tạo plate
        plate = DetectionService.get_or_create_plate(db, detection_data.plate_text)
        
        # Kiểm tra plate có trong DB không → auto verify
        is_verified = plate.owner_name is not None or plate.province is not None
        
        # Tạo detection
        detection = Detection(
            plate_id=plate.id,
            user_id=user_id,
            confidence=detection_data.confidence,
            raw_text=detection_data.raw_text or detection_data.plate_text,
            crop_image_path=detection_data.crop_image_path,
            is_verified=is_verified
        )
        
        db.add(detection)
        db.commit()
        db.refresh(detection)
        
        print(f"[DETECTION] Saved: {plate.plate_text} (verified={is_verified}, tracker={tracker_id})")
        
        return detection
    
    @staticmethod
    def get_recent_detections(
        db: Session,
        limit: int = 50,
        verified_only: bool = False
    ) -> List[DetectionResponse]:
        """
        Lấy danh sách detections gần nhất
        """
        query = db.query(Detection).join(Plate)
        
        if verified_only:
            query = query.filter(Detection.is_verified == True)
        
        detections = query.order_by(desc(Detection.timestamp)).limit(limit).all()
        
        # Convert to response schema
        results = []
        for det in detections:
            plate = det.plate if hasattr(det, 'plate') else db.query(Plate).filter(Plate.id == det.plate_id).first()
            
            results.append(DetectionResponse(
                id=det.id,
                plate_id=det.plate_id,
                user_id=det.user_id,
                confidence=det.confidence,
                timestamp=det.timestamp,
                raw_text=det.raw_text,
                crop_image_path=det.crop_image_path,
                is_verified=det.is_verified,
                plate_text=plate.plate_text if plate else "Unknown",
                plate_province=plate.province if plate else None,
                plate_owner=plate.owner_name if plate else None,
                is_blacklisted=plate.is_blacklisted if plate else False,
                blacklist_reason=plate.blacklist_reason if plate else None
            ))
        
        return results
    
    @staticmethod
    def get_latest_detection(db: Session) -> Optional[DetectionResponse]:
        """
        Lấy detection mới nhất (cái cuối cùng được detect)
        """
        detection = (
            db.query(Detection)
            .join(Plate)
            .order_by(desc(Detection.timestamp))
            .first()
        )
        
        if not detection:
            return None
        
        plate = detection.plate if hasattr(detection, 'plate') else db.query(Plate).filter(Plate.id == detection.plate_id).first()
        
        return DetectionResponse(
            id=detection.id,
            plate_id=detection.plate_id,
            user_id=detection.user_id,
            confidence=detection.confidence,
            timestamp=detection.timestamp,
            raw_text=detection.raw_text,
            crop_image_path=detection.crop_image_path,
            is_verified=detection.is_verified,
            plate_text=plate.plate_text if plate else "Unknown",
            plate_province=plate.province if plate else None,
            plate_owner=plate.owner_name if plate else None,
            is_blacklisted=plate.is_blacklisted if plate else False,
            blacklist_reason=plate.blacklist_reason if plate else None
        )
    
    @staticmethod
    def get_blacklisted_detections(db: Session, limit: int = 20) -> List[DetectionResponse]:
        """
        Lấy danh sách xe blacklist được detect
        """
        detections = (
            db.query(Detection)
            .join(Plate)
            .filter(Plate.is_blacklisted == True)
            .order_by(desc(Detection.timestamp))
            .limit(limit)
            .all()
        )
        
        return [DetectionResponse.from_orm(d) for d in detections]
    
    @staticmethod
    def get_detection_stats(db: Session) -> dict:
        """
        Lấy thống kê detection
        """
        today = datetime.now().date()
        
        return {
            "total_detections": db.query(Detection).count(),
            "verified_detections": db.query(Detection).filter(Detection.is_verified == True).count(),
            "blacklisted_detections": (
                db.query(Detection)
                .join(Plate)
                .filter(Plate.is_blacklisted == True)
                .count()
            ),
            "unique_plates": db.query(Plate).count(),
            "today_detections": (
                db.query(Detection)
                .filter(func.date(Detection.timestamp) == today)
                .count()
            )
        }