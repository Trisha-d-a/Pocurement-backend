from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, database, schemas

router = APIRouter(prefix="/boq", tags=["BOQ"])

@router.post("/", response_model=schemas.Boq)
def create_boq(boq: schemas.BoqCreate, db: Session = Depends(database.get_db)):
    boq_item = models.BOQ(project_id=boq.project_id, material_id=boq.material_id, quantity=boq.quantity)
    db.add(boq_item)
    db.commit()
    db.refresh(boq_item)
    return boq_item

@router.get("/", response_model=list[schemas.Boq])
def get_boq(db: Session = Depends(database.get_db)):
    return db.query(models.BOQ).all()

@router.get("/{boq_id}", response_model=schemas.Boq)
def get_boq_item(boq_id: int, db: Session = Depends(database.get_db)):
    boq_item = db.query(models.BOQ).filter(models.BOQ.id == boq_id).first()
    if not boq_item:
        raise HTTPException(status_code=404, detail="BOQ item not found")
    return boq_item

@router.put("/{boq_id}", response_model=schemas.Boq)
def update_boq(boq_id: int, boq: schemas.BoqCreate, db: Session = Depends(database.get_db)):
    db_boq = db.query(models.BOQ).filter(models.BOQ.id == boq_id).first()
    if not db_boq:
        raise HTTPException(status_code=404, detail="BOQ item not found")
    db_boq.project_id = boq.project_id
    db_boq.material_id = boq.material_id
    db_boq.quantity = boq.quantity
    db.commit()
    db.refresh(db_boq)
    return db_boq

@router.delete("/{boq_id}")
def delete_boq(boq_id: int, db: Session = Depends(database.get_db)):
    boq_item = db.query(models.BOQ).filter(models.BOQ.id == boq_id).first()
    if not boq_item:
        raise HTTPException(status_code=404, detail="BOQ item not found")
    db.delete(boq_item)
    db.commit()
    return {"message": f"BOQ item {boq_id} deleted successfully"}
