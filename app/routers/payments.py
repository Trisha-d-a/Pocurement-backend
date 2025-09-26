from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, database

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", response_model=schemas.Payment, status_code=status.HTTP_201_CREATED)
def create_payment(payment: schemas.PaymentCreate, db: Session = Depends(database.get_db)):
    # ensure purchase order exists
    if not db.get(models.PurchaseOrder, payment.purchase_order_id):
        raise HTTPException(status_code=404, detail="Purchase order not found")

    db_payment = models.Payment(**payment.model_dump())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


@router.get("/", response_model=list[schemas.Payment])
def get_payments(db: Session = Depends(database.get_db)):
    return db.query(models.Payment).all()


@router.get("/{payment_id}", response_model=schemas.Payment)
def get_payment(payment_id: int, db: Session = Depends(database.get_db)):
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.put("/{payment_id}", response_model=schemas.Payment)
def update_payment(payment_id: int, payment_data: schemas.PaymentCreate, db: Session = Depends(database.get_db)):
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # validate purchase order if changed
    if not db.get(models.PurchaseOrder, payment_data.purchase_order_id):
        raise HTTPException(status_code=404, detail="Purchase order not found")

    for field, value in payment_data.model_dump().items():
        setattr(payment, field, value)

    db.commit()
    db.refresh(payment)
    return payment


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(payment_id: int, db: Session = Depends(database.get_db)):
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    db.delete(payment)
    db.commit()
    return None
