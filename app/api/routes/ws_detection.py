from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.detection_service import DetectionService, detection_tracker
from app.api.dependencies import get_active_user
from app.schemas.detection import DetectionCreate
from app.utils.format_plate import standardize_plate
from app.utils import validate_plate
import cv2
import supervision as sv
from app.ai.yolo import model, FRAME_SKIP, MIN_PLATE_AREA
from app.ai.ocr_worker import load_ocr_model
from queue import Queue
import threading
import os
import time
from datetime import datetime

router = APIRouter(prefix="/stream", tags=["Streaming"])
templates = Jinja2Templates(directory="app/templates")

# ✅ GLOBAL CAMERA STATE (singleton pattern)
class CameraManager:
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
        
        self.ocr = load_ocr_model()
        self.byte_tracker = sv.ByteTrack()
        self.ocr_cache = {}
        self.ocr_queue = Queue()
        self.ocr_results = {}
        self.running = False
        self.latest_plates = []
        self.latest_plates_lock = threading.Lock()
        self.cap = None
        self._initialized = True
        
        # Start OCR worker thread
        self.start_ocr_worker()
    
    def start_ocr_worker(self):
        """Background thread xử lý OCR không block camera stream"""
        self.running = True
        
        def worker():
            while self.running:
                if not self.ocr_queue.empty():
                    plate_id, image_path = self.ocr_queue.get()
                    try:
                        result_ocr = self.ocr.predict(image_path)
                        if result_ocr and len(result_ocr) > 0 and 'rec_texts' in result_ocr[0]:
                            text = ''.join(result_ocr[0]['rec_texts']) if result_ocr[0]['rec_texts'] else "No text"
                        else:
                            text = "No text"
                        
                        # ✅ Chuẩn hóa biển số
                        if text != "No text" and text != "Error":
                            text = standardize_plate(text)
                        
                        self.ocr_results[plate_id] = text
                        self.ocr_cache[plate_id] = text
                        
                        # Xóa file tạm
                        if os.path.exists(image_path):
                            os.remove(image_path)
                    except Exception as e:
                        self.ocr_results[plate_id] = "Error"
                        print(f"OCR Error: {e}")
                else:
                    time.sleep(0.01)
        
        self.ocr_thread = threading.Thread(target=worker, daemon=True)
        self.ocr_thread.start()
    
    def get_camera(self):
        """Lazy load camera"""
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                # Warm up camera
                for _ in range(5):
                    self.cap.read()
        return self.cap
    
    def release_camera(self):
        """Release camera resources"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def add_detected_plate(self, plate_text, confidence, tracker_id=None, crop_path=None):
        """Thread-safe thêm plate mới và hiển thị (với format chuẩn)"""
        if "Processing" in plate_text or "Small" in plate_text or "Error" in plate_text:
            return
        
        # Chuẩn hóa plate text để hiển thị
        formatted_plate = standardize_plate(plate_text)
        
        # Validate format
        validation_result = validate_plate(formatted_plate)
        if not validation_result['valid']:
            print(f"[DISPLAY] ✗ Skip invalid plate: {formatted_plate}")
            return  # ❌ Không thêm vào danh sách hiển thị nếu invalid
        
        with self.latest_plates_lock:
            # Kiểm tra trùng lặp (trong 60s gần nhất)
            now = datetime.now()
            self.latest_plates = [
                p for p in self.latest_plates 
                if (now - p['timestamp']).total_seconds() < 60  # Giữ 1 phút
            ]
            
            # Thêm plate mới (với format chuẩn)
            self.latest_plates.insert(0, {
                "plate": formatted_plate,  # ✅ Hiển thị plate đã format
                "confidence": confidence,
                "timestamp": now,
                "tracker_id": tracker_id
            })
            
            # Giới hạn 50 plates
            if len(self.latest_plates) > 50:
                self.latest_plates = self.latest_plates[:50]
    
    def save_detection_to_db(self, db: Session, plate_text: str, confidence: float, tracker_id: int = None, crop_path: str = None):
        """
        Lưu detection vào database với anti-spam và validation
        Reject invalid plates - không lưu nếu format không hợp lệ
        """
        try:
            # Chuẩn hóa trước
            standardized_plate = standardize_plate(plate_text)
            
            # Validate plate format trước khi lưu
            validation_result = validate_plate(standardized_plate)
            if not validation_result['valid']:
                print(f"[DB] ✗ REJECTED - Invalid plate format: {standardized_plate} - {validation_result['error']}")
                return  # ❌ REJECT - không lưu vào DB
            
            # Plate hợp lệ - lưu vào DB
            detection_data = DetectionCreate(
                plate_text=validation_result['plate'],  # Dùng standardized plate
                confidence=confidence,
                raw_text=plate_text,  # Giữ raw text gốc
                crop_image_path=crop_path,
                tracker_id=tracker_id
            )
            
            # Service sẽ tự động check cooldown
            detection = DetectionService.create_detection(
                db=db,
                detection_data=detection_data,
                user_id=None,  # Có thể thêm user_id nếu có authentication
                tracker_id=tracker_id
            )
            
            if detection:
                print(f"[DB] ✓ Saved detection: {validation_result['plate']} (ID: {detection.id})")
            else:
                print(f"[DB] ⏭️  Skipped (cooldown): {validation_result['plate']}")
                
        except Exception as e:
            print(f"[DB] ✗ Error saving detection: {e}")
            import traceback
            traceback.print_exc()
    
    def get_latest_plates(self):
        """Thread-safe lấy danh sách plates"""
        with self.latest_plates_lock:
            return self.latest_plates.copy()
    
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        self.release_camera()

# Global camera manager
camera_manager = CameraManager()

def generate_frames(db: Session):
    """
    Generator function để stream MJPEG frames
    """
    cap = camera_manager.get_camera()
    if not cap.isOpened():
        print("Cannot open camera")
        return
    
    frame_count = 0
    prev_detections = None
    prev_labels = []
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame")
                time.sleep(0.1)
                continue
            
            frame_count += 1
            labels = []
            detections = prev_detections
            
            # ✅ Detection mỗi FRAME_SKIP frames
            if frame_count % FRAME_SKIP == 0:
                result = model(frame)[0]
                detections = sv.Detections.from_ultralytics(result)
                detections = camera_manager.byte_tracker.update_with_detections(detections)
                
                labels = []
                
                for i in range(len(detections)):
                    x1, y1, x2, y2 = map(int, detections.xyxy[i])
                    class_id = detections.class_id[i]
                    confidence = detections.confidence[i]
                    class_name = model.model.names[class_id]
                    
                    label = f"{class_name} {confidence:.2f}"
                    
                    if class_name == 'License_Plate':
                        # Kiểm tra kích thước
                        plate_area = (x2 - x1) * (y2 - y1)
                        if plate_area < MIN_PLATE_AREA:
                            labels.append("Small plate")
                            continue
                        
                        # ✅ LẤY TRACKER ID từ ByteTrack
                        tracker_id = None
                        if hasattr(detections, 'tracker_id') and detections.tracker_id is not None:
                            tracker_id = int(detections.tracker_id[i])
                            plate_id = f"plate_{tracker_id}"
                        else:
                            plate_id = f"plate_{x1}_{y1}_{x2}_{y2}"
                        
                        # OCR logic với cache
                        if plate_id in camera_manager.ocr_cache:
                            label = camera_manager.ocr_cache[plate_id]
                        elif plate_id in camera_manager.ocr_results:
                            label = camera_manager.ocr_results[plate_id]
                            if label not in ["Processing...", "Error"]:
                                camera_manager.ocr_cache[plate_id] = label
                        else:
                            # Crop và OCR
                            cropped_image = frame[y1:y2, x1:x2]
                            
                            if cropped_image.size > 0:
                                height, width = cropped_image.shape[:2]
                                if height < 50:
                                    scale_factor = 50 / height
                                    new_width = int(width * scale_factor)
                                    cropped_image = cv2.resize(cropped_image, (new_width, 50))
                                
                                # Tăng contrast
                                cropped_image = cv2.convertScaleAbs(cropped_image, alpha=1.2, beta=10)
                                
                                # Lưu và queue OCR
                                os.makedirs('crop', exist_ok=True)
                                image_path = f'crop/output_{plate_id}.png'
                                cv2.imwrite(image_path, cropped_image)
                                
                                if plate_id not in camera_manager.ocr_results:
                                    camera_manager.ocr_queue.put((plate_id, image_path))
                                    camera_manager.ocr_results[plate_id] = "Processing..."
                                
                                label = "Processing..."
                            else:
                                label = "Empty crop"
                        
                        # Thêm vào danh sách detected plates
                        if label not in ["Processing...", "Small plate", "Empty crop", "Error"]:
                            camera_manager.add_detected_plate(label, float(confidence), tracker_id, image_path if 'image_path' in locals() else None)
                            
                            # ✅ LƯU VÀO DATABASE (async trong background)
                            threading.Thread(
                                target=camera_manager.save_detection_to_db,
                                args=(db, label, float(confidence), tracker_id, image_path if 'image_path' in locals() else None),
                                daemon=True
                            ).start()
                    
                    labels.append(label)
                
                prev_detections = detections
                prev_labels = labels
            else:
                labels = prev_labels
            
            # ✅ VẼ ANNOTATION
            annotated_frame = frame.copy()
            if detections is not None and len(detections) > 0:
                for i, label in enumerate(labels):
                    x1, y1, x2, y2 = map(int, detections.xyxy[i])
                    
                    # Vẽ bbox
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    
                    # Vẽ label
                    (text_width, text_height), baseline = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
                    )
                    cv2.rectangle(
                        annotated_frame,
                        (x1, y1 - text_height - 10),
                        (x1 + text_width + 10, y1),
                        (0, 255, 0),
                        -1
                    )
                    cv2.putText(
                        annotated_frame,
                        label,
                        (x1 + 5, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 0),
                        2
                    )
            
            # ✅ Encode frame as JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 75]
            ret, buffer = cv2.imencode('.jpg', annotated_frame, encode_param)
            
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()
            
            # ✅ Yield frame trong MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Delay nhỏ để tránh overwhelm
            time.sleep(0.01)
    
    except Exception as e:
        print(f"Stream error: {e}")
        import traceback
        traceback.print_exc()

@router.get("/video_feed")
async def video_feed(db: Session = Depends(get_db)):
    """
    MJPEG video stream endpoint
    Truy cập: http://localhost:8000/stream/video_feed
    Không bắt auth vì img tag không thể gửi header
    """
    return StreamingResponse(
        generate_frames(db),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/plates")
async def get_latest_plates():
    """
    API để lấy danh sách plates mới nhất
    Frontend poll endpoint này mỗi 1s
    Không bắt auth vì frontend gửi token qua header (fetch)
    """
    plates = camera_manager.get_latest_plates()
    return {
        "plates": plates,
        "count": len(plates)
    }

@router.get("/latest-detection")
async def get_latest_detection(db: Session = Depends(get_db)):
    """
    API để lấy detection cuối cùng (biển số mới nhất được detect)
    Frontend dùng endpoint này cho Latest Detection panel
    Không bắt auth vì frontend gửi token qua header (fetch)
    """
    try:
        detection = DetectionService.get_latest_detection(db)
        if detection:
            return {
                "success": True,
                "detection": detection
            }
        else:
            return {
                "success": True,
                "detection": None
            }
    except Exception as e:
        print(f"Error fetching latest detection: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "detection": None,
            "error": str(e)
        }

@router.get("/detections-history")
async def get_detections_history(limit: int = 50, search: str = "", db: Session = Depends(get_db)):
    """
    API để lấy detection history từ DATABASE
    Parameters:
    - limit: số lượng records (default 50)
    - search: tìm kiếm theo plate_text (optional)
    
    Frontend dùng endpoint này cho Recent Detections Table
    Không bắt auth vì frontend gửi token qua header (fetch)
    """
    try:
        detections = DetectionService.get_recent_detections(db, limit=limit)
        
        # Filter by search text nếu có
        if search:
            search_upper = search.strip().upper()
            detections = [d for d in detections if search_upper in d.plate_text.upper()]
        
        return {
            "success": True,
            "detections": detections,
            "count": len(detections)
        }
    except Exception as e:
        print(f"Error fetching detections: {e}")
        return {
            "success": False,
            "detections": [],
            "error": str(e)
        }

@router.get("/", response_class=HTMLResponse)
async def stream_dashboard(request: Request):
    """
    Render dashboard HTML với MJPEG stream
    Truy cập: http://localhost:8000/stream/
    """
    return templates.TemplateResponse("stream_dashboard.html", {"request": request})