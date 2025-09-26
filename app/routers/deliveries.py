from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, database

router = APIRouter(prefix="/deliveries", tags=["Deliveries"])

# Create Delivery
@router.post("/", response_model=schemas.Delivery)
def create_delivery(delivery: schemas.DeliveryCreate, db: Session = Depends(database.get_db)):
    db_delivery = models.Delivery(**delivery.dict())
    db.add(db_delivery)
    db.commit()
    db.refresh(db_delivery)
    return db_delivery

# Get all Deliveries
@router.get("/", response_model=list[schemas.Delivery])
def get_deliveries(db: Session = Depends(database.get_db)):
    return db.query(models.Delivery).all()

# Get a single Delivery
@router.get("/{delivery_id}", response_model=schemas.Delivery)
def get_delivery(delivery_id: int, db: Session = Depends(database.get_db)):
    delivery = db.query(models.Delivery).filter(models.Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery

# Update a Delivery
@router.put("/{delivery_id}", response_model=schemas.Delivery)
def update_delivery(delivery_id: int, delivery_data: schemas.DeliveryCreate, db: Session = Depends(database.get_db)):
    delivery = db.query(models.Delivery).filter(models.Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")

    delivery.purchase_order_id = delivery_data.purchase_order_id
    delivery.delivery_date = delivery_data.delivery_date
    delivery.status = delivery_data.status
    delivery.received_quantity = delivery_data.received_quantity
    db.commit()
    db.refresh(delivery)
    return delivery

# Delete a Delivery
@router.delete("/{delivery_id}")
def delete_delivery(delivery_id: int, db: Session = Depends(database.get_db)):
    delivery = db.query(models.Delivery).filter(models.Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    db.delete(delivery)
    db.commit()
    return {"message": f"Delivery {delivery_id} deleted successfully"}
