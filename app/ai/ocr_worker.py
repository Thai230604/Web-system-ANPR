from paddleocr import PaddleOCR
from queue import Queue
import threading, time, os

# ocr = PaddleOCR(use_angle_cls=True, lang='en')
def load_ocr_model():
    print("Preloading PaddleOCR model...")
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    return ocr
ocr_queue = Queue()
ocr_results = {}
ocr_cache = {}

def worker():
    while True:
        if not ocr_queue.empty():
            plate_id, image_path = ocr_queue.get()
            try:
                result_ocr = ocr.predict(image_path)
                if result_ocr and 'rec_texts' in result_ocr[0]:
                    text = ''.join(result_ocr[0]['rec_texts']) if result_ocr[0]['rec_texts'] else "No text"
                else:
                    text = "No text"
                ocr_results[plate_id] = text
                ocr_cache[plate_id] = text
            except Exception as e:
                print(f"OCR worker error: {e}")
                ocr_results[plate_id] = "Error"
        time.sleep(0.01)

# Start thread once
threading.Thread(target=worker, daemon=True).start()

__all__ = ['ocr', 'ocr_queue', 'ocr_results', 'ocr_cache', 'worker']
