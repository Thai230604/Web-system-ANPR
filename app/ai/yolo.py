from ultralytics import YOLO
import supervision as sv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, '..', '..', 'model', 'best (2).pt')

model = YOLO(MODEL_PATH)

# Tracker + annotators
box_annotator = sv.BoxAnnotator(thickness=2)
label_annotator = sv.LabelAnnotator(text_thickness=2, text_scale=1.2)
byte_tracker = sv.ByteTrack()

FRAME_SKIP = 3
MIN_PLATE_AREA = 1000
