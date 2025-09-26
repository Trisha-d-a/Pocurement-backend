from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, database

router = APIRouter(prefix="/vendors", tags=["Vendors"])


@router.post("/", response_model=schemas.Vendor, status_code=status.HTTP_201_CREATED)
def create_vendor(vendor: schemas.VendorCreate, db: Session = Depends(database.get_db)):
    db_vendor = models.Vendor(**vendor.model_dump())
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    return db_vendor


@router.get("/", response_model=List[schemas.Vendor])
def get_vendors(db: Session = Depends(database.get_db)):
    # Keep vendors ordered by ID
    return db.query(models.Vendor).order_by(models.Vendor.id.asc()).all()


@router.get("/{vendor_id}", response_model=schemas.Vendor)
def get_vendor(vendor_id: int, db: Session = Depends(database.get_db)):
    vendor = db.query(models.Vendor).filter(models.Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    return vendor


@router.put("/{vendor_id}", response_model=schemas.Vendor)
def update_vendor(vendor_id: int, vendor_update: schemas.VendorUpdate, db: Session = Depends(database.get_db)):
    db_vendor = db.query(models.Vendor).filter(models.Vendor.id == vendor_id).first()
    if not db_vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")

    update_data = vendor_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vendor, field, value)

    db.commit()
    db.refresh(db_vendor)
    return db_vendor


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(vendor_id: int, db: Session = Depends(database.get_db)):
    vendor = db.query(models.Vendor).filter(models.Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    db.delete(vendor)
    db.commit()
    return None
