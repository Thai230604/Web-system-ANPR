from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.plate import PlateCreate, PlateUpdate, PlateOut
from app.services.plate_services import (
    get_all_plates, get_plate_by_text, create_plate, update_plate, delete_plate
)
from app.utils import validate_plate, standardize_plate

router = APIRouter(prefix="/api/plates", tags=["plates"])

@router.get("/", response_model=list[PlateOut])
def list_plates(db: Session = Depends(get_db)):
    return get_all_plates(db)

@router.post("/", response_model=PlateOut)
def create_new_plate(plate_in: PlateCreate, db: Session = Depends(get_db)):
    # Validate plate format
    validation_result = validate_plate(plate_in.plate_text)
    if not validation_result['valid']:
        raise HTTPException(
            status_code=400, 
            detail=f"Biển số không hợp lệ: {validation_result['error']}"
        )
    
    standardized_plate = validation_result['plate']
    
    # Check if plate already exists
    plate = get_plate_by_text(db, standardized_plate)
    if plate:
        raise HTTPException(status_code=400, detail="Biển số đã tồn tại")
    
    # Create new plate with standardized text
    plate_in.plate_text = standardized_plate
    return create_plate(db, plate_in)

@router.put("/{plate_id}", response_model=PlateOut)
def update_plate_info(plate_id: int, plate_in: PlateUpdate, db: Session = Depends(get_db)):
    plate = update_plate(db, plate_id, plate_in)
    if not plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    return plate

@router.delete("/{plate_id}")
def remove_plate(plate_id: int, db: Session = Depends(get_db)):
    ok = delete_plate(db, plate_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Plate not found")
    return {"message": "Deleted successfully"}
