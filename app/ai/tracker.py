from app.ai.yolo import byte_tracker, box_annotator, label_annotator, MIN_PLATE_AREA

def track_and_annotate(frame, detections, labels):
    # Update tracker
    detections = byte_tracker.update_with_detections(detections)
    annotated_frame = box_annotator.annotate(frame.copy(), detections)
    annotated_frame = label_annotator.annotate(annotated_frame, detections, labels)
    return annotated_frame, detections
