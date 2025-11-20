from sqlalchemy.orm import Session
from app.models.plate import Plate
from app.schemas.plate import PlateCreate, PlateUpdate

def get_plate_by_text(db: Session, plate_text: str):
    return db.query(Plate).filter(Plate.plate_text == plate_text).first()

def get_all_plates(db: Session):
    return db.query(Plate).all()

def create_plate(db: Session, plate_in: PlateCreate):
    plate = Plate(**plate_in.dict())
    db.add(plate)
    db.commit()
    db.refresh(plate)
    return plate

def update_plate(db: Session, plate_id: int, plate_in: PlateUpdate):
    plate = db.query(Plate).filter(Plate.id == plate_id).first()
    if not plate:
        return None

    for key, value in plate_in.dict(exclude_unset=True).items():
        setattr(plate, key, value)
    
    db.commit()
    db.refresh(plate)
    return plate

def delete_plate(db: Session, plate_id: int):
    plate = db.query(Plate).filter(Plate.id == plate_id).first()
    if not plate:
        return False

    db.delete(plate)
    db.commit()
    return True
