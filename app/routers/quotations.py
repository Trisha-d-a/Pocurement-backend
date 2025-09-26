from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, database

router = APIRouter(prefix="/quotations", tags=["Quotations"])

# Create a quotation
@router.post("/", response_model=schemas.Quotation)
def create_quotation(quotation: schemas.QuotationCreate, db: Session = Depends(database.get_db)):
    db_project = db.get(models.Project, quotation.project_id)
    db_material = db.get(models.Material, quotation.material_id)
    db_vendor = db.get(models.Vendor, quotation.vendor_id)
    if not db_project or not db_material or not db_vendor:
        raise HTTPException(status_code=400, detail="Invalid project, material, or vendor ID")

    db_quotation = models.Quotation(**quotation.model_dump())
    db.add(db_quotation)
    db.commit()
    db.refresh(db_quotation)
    return db_quotation

# Get all quotations
@router.get("/", response_model=list[schemas.Quotation])
def get_all_quotations(db: Session = Depends(database.get_db)):
    return db.query(models.Quotation).all()

# Get a specific quotation
@router.get("/{quotation_id}", response_model=schemas.Quotation)
def get_quotation(quotation_id: int, db: Session = Depends(database.get_db)):
    quotation = db.query(models.Quotation).filter(models.Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return quotation

# Get quotations for a material
@router.get("/material/{material_id}", response_model=list[schemas.Quotation])
def get_quotations_for_material(material_id: int, db: Session = Depends(database.get_db)):
    return db.query(models.Quotation).filter(models.Quotation.material_id == material_id).all()

# Update a quotation
@router.put("/{quotation_id}", response_model=schemas.Quotation)
def update_quotation(quotation_id: int, quotation: schemas.QuotationCreate, db: Session = Depends(database.get_db)):
    db_quotation = db.query(models.Quotation).filter(models.Quotation.id == quotation_id).first()
    if not db_quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    db_quotation.project_id = quotation.project_id
    db_quotation.material_id = quotation.material_id
    db_quotation.vendor_id = quotation.vendor_id
    db_quotation.price = quotation.price
    db_quotation.date = quotation.date
    db_quotation.payment_terms = quotation.payment_terms
    db.commit()
    db.refresh(db_quotation)
    return db_quotation

# Delete a quotation
@router.delete("/{quotation_id}")
def delete_quotation(quotation_id: int, db: Session = Depends(database.get_db)):
    quotation = db.query(models.Quotation).filter(models.Quotation.id == quotation_id).first()
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    db.delete(quotation)
    db.commit()
    return {"message": f"Quotation {quotation_id} deleted successfully"}
