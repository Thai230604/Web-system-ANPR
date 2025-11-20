from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.routes import auth, plates, ws_detection, detections
from app.api.dependencies import get_active_user
from app.core.database import engine, Base
import asyncio
import os
from app.services.plate_services import get_all_plates
from app.core.database import get_db

print("[STARTUP] Initializing application...")

# Create tables on startup
print("[STARTUP] Creating database tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("[STARTUP] Database tables created successfully!")
except Exception as e:
    print(f"[STARTUP] Database creation error: {e}")

# # Warmup YOLO model
# print("[STARTUP] Warming up YOLO model...")
# try:
#     import numpy as np
#     from app.ai.yolo import model
#     dummy_frame = np.ones((640, 640, 3), dtype=np.uint8) * 255
#     _ = model(dummy_frame)
#     print("[STARTUP] YOLO model warmup completed!")
# except Exception as e:
#     print(f"[STARTUP] YOLO warmup error (non-critical): {e}")

# # Import OCR to trigger warmup
# print("[STARTUP] Warming up OCR model...")
# try:
#     from app.ai.ocr_worker import load_ocr_model
#     ocr_model = load_ocr_model()
#     print("[STARTUP] OCR model warmup completed!")
# except Exception as e:
#     print(f"[STARTUP] OCR warmup error (non-critical): {e}")

app = FastAPI(title="ANPR-Webcam Backend")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

origins = ["http://localhost:5173", "http://localhost:8000", "http://127.0.0.1:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(plates.router)
app.include_router(ws_detection.router)
# app.include_router(detections.router)

# HTML Routes for Server-Side Rendering
# Lưu ý: Auth check được làm ở client (auth.js) + API calls
@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard")
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# @app.get("/plates")
# def plates_page(request: Request):
#     return templates.TemplateResponse("plates.html", {"request": request})
@app.get("/plates")
async def plates_page(request: Request, db=Depends(get_db)):
    plates = get_all_plates(db)  # lấy dữ liệu từ DB ngay ở server
    return templates.TemplateResponse(
        "plates.html",
        {
            "request": request,
            "initial_plates": plates  # truyền thẳng vào template
        }
    )

@app.get("/history")
def history_page(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})

@app.get("/reports")
def reports_page(request: Request):
    return templates.TemplateResponse("reports.html", {"request": request})

@app.get("/api")
def api_root():
    return {"message": "API is running!"}