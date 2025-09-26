from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, database

router = APIRouter(prefix="/purchase_orders", tags=["Purchase Orders"])


@router.post("/", response_model=schemas.PurchaseOrder, status_code=status.HTTP_201_CREATED)
def create_purchase_order(po: schemas.PurchaseOrderCreate, db: Session = Depends(database.get_db)):
    # validate foreign keys exist
    if not db.get(models.Project, po.project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    if not db.get(models.Vendor, po.vendor_id):
        raise HTTPException(status_code=404, detail="Vendor not found")
    if not db.get(models.Material, po.material_id):
        raise HTTPException(status_code=404, detail="Material not found")

    db_po = models.PurchaseOrder(**po.model_dump())
    db.add(db_po)
    db.commit()
    db.refresh(db_po)
    return db_po


@router.get("/", response_model=list[schemas.PurchaseOrder])
def get_purchase_orders(db: Session = Depends(database.get_db)):
    return db.query(models.PurchaseOrder).all()


@router.get("/{po_id}", response_model=schemas.PurchaseOrder)
def get_purchase_order(po_id: int, db: Session = Depends(database.get_db)):
    db_po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
    if not db_po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return db_po


@router.put("/{po_id}", response_model=schemas.PurchaseOrder)
def update_purchase_order(po_id: int, po_data: schemas.PurchaseOrderCreate, db: Session = Depends(database.get_db)):
    db_po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
    if not db_po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    # validate foreign keys on update as well
    if not db.get(models.Project, po_data.project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    if not db.get(models.Vendor, po_data.vendor_id):
        raise HTTPException(status_code=404, detail="Vendor not found")
    if not db.get(models.Material, po_data.material_id):
        raise HTTPException(status_code=404, detail="Material not found")

    for field, value in po_data.model_dump().items():
        setattr(db_po, field, value)

    db.commit()
    db.refresh(db_po)
    return db_po


@router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase_order(po_id: int, db: Session = Depends(database.get_db)):
    db_po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
    if not db_po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    db.delete(db_po)
    db.commit()
    return None
