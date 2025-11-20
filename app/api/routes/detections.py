# from fastapi import APIRouter, UploadFile, File, HTTPException
# from fastapi.responses import JSONResponse
# import cv2
# import numpy as np
# import os
# import base64
# from io import BytesIO
# from PIL import Image
# import supervision as sv
# from app.ai.yolo import model, box_annotator, label_annotator, byte_tracker, MIN_PLATE_AREA
# from app.ai.ocr_worker import load_ocr_model
# from app.schemas.detection import ProcessImageResponse, DetectOnlyResponse, DetectionResult

# router = APIRouter(prefix="/api/detections", tags=["Detections"])
# ocr = load_ocr_model()

# @router.post("/process-image")
# async def process_image(file: UploadFile = File(...)):
#     """
#     Nhận hình ảnh, thực hiện detection và OCR trên license plate
#     """
#     try:
#         # Đọc file upload
#         contents = await file.read()
#         nparr = np.frombuffer(contents, np.uint8)
#         frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
#         if frame is None:
#             raise HTTPException(status_code=400, detail="Invalid image file")
        
#         # YOLO detection
#         result = model(frame)[0]
#         detections = sv.Detections.from_ultralytics(result)
#         detections = byte_tracker.update_with_detections(detections)
        
#         labels = []
#         plates_data = []
        
#         # Xử lý từng detection
#         for i in range(len(detections)):
#             x1, y1, x2, y2 = detections.xyxy[i]
#             class_id = detections.class_id[i]
#             confidence = detections.confidence[i]
#             tracker_id = detections.tracker_id[i]
            
#             class_name = model.model.names[class_id]
#             label = f"{class_name} {confidence:.2f}"
#             # Nếu là License Plate, thực hiện OCR
#             if class_name == 'License_Plate':
#                 x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
#                 # Kiểm tra kích thước plate
#                 plate_area = (x2 - x1) * (y2 - y1)
#                 if plate_area < MIN_PLATE_AREA:
#                     label = "Small plate"
#                     labels.append(label)
#                     plates_data.append({
#                         "bbox": [x1, y1, x2, y2],
#                         "text": "Small plate",
#                         "confidence": float(confidence)
#                     })
#                     continue
                
#                 # Crop plate từ frame
#                 cropped_image = frame[y1:y2, x1:x2]
                
#                 # Phóng to ảnh để cải thiện OCR
#                 if cropped_image.size > 0:
#                     cropped_image = cv2.resize(
#                         cropped_image, 
#                         (cropped_image.shape[1] * 2, cropped_image.shape[0] * 2)
#                     )
                    
#                     # Lưu ảnh tạm
#                     os.makedirs('crop', exist_ok=True)
#                     image_path = f'crop/temp_plate_{tracker_id}.png'
#                     cv2.imwrite(image_path, cropped_image)
                    
#                     # Thực hiện OCR
#                     try:
#                         result_ocr = ocr.predict(image_path)
#                         if result_ocr and len(result_ocr) > 0 and 'rec_texts' in result_ocr[0]:
#                             # Extract text from rec_texts
#                             rec_texts = result_ocr[0]['rec_texts']
#                             plate_text = ''.join(rec_texts) if rec_texts else "No text"
#                             label = plate_text
#                         else:
#                             label = "No text"
#                     except Exception as e:
#                         label = f"OCR Error: {str(e)}"
                    
#                     # Xóa file tạm sau khi OCR xong
#                     if os.path.exists(image_path):
#                         os.remove(image_path)
            
#             labels.append(label)
#             plates_data.append({
#                 "bbox": [x1, y1, x2, y2],
#                 "text": label,
#                 "confidence": float(confidence),
#                 "class": class_name
#             })
        
#         # Annotate frame
#         annotated_frame = frame.copy()
#         annotated_frame = box_annotator.annotate(annotated_frame, detections)
#         annotated_frame = label_annotator.annotate(annotated_frame, detections, labels)
        
#         # Encode frame to base64
#         _, buffer = cv2.imencode('.jpg', annotated_frame)
#         frame_b64 = base64.b64encode(buffer).decode('utf-8')
        
#         return JSONResponse({
#             "success": True,
#             "frame": frame_b64,
#             "detections": plates_data,
#             "total_detections": len(detections)
#         })
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


# @router.post("/detect-only")
# async def detect_only(file: UploadFile = File(...)):
#     """
#     Nhận hình ảnh, chỉ thực hiện detection (không OCR)
#     """
#     try:
#         contents = await file.read()
#         nparr = np.frombuffer(contents, np.uint8)
#         frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
#         if frame is None:
#             raise HTTPException(status_code=400, detail="Invalid image file")
        
#         # YOLO detection
#         result = model(frame)[0]
#         detections = sv.Detections.from_ultralytics(result)
        
#         detections_data = []
#         for i in range(len(detections)):
#             x1, y1, x2, y2 = detections.xyxy[i]
#             class_id = detections.class_id[i]
#             confidence = detections.confidence[i]
            
#             detections_data.append({
#                 "bbox": [int(x1), int(y1), int(x2), int(y2)],
#                 "class": model.model.names[class_id],
#                 "confidence": float(confidence)
#             })
        
#         return JSONResponse({
#             "success": True,
#             "detections": detections_data,
#             "total_detections": len(detections)
#         })
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
