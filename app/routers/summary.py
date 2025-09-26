from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, database

router = APIRouter(prefix="/summary", tags=["Summary"])

@router.get("/project_status/{project_id}")
def get_project_status(project_id: int, db: Session = Depends(database.get_db)):
    try:
        boq_count = db.query(models.BOQ).filter(models.BOQ.project_id == project_id).count()
        po_count = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.project_id == project_id).count()
        return {"BOQ Items": boq_count, "Purchase Orders": po_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching project status: {str(e)}")

@router.get("/procurement_logs")
def get_procurement_logs(db: Session = Depends(database.get_db)):
    try:
        logs = {
            "projects": db.query(models.Project).count(),
            "materials": db.query(models.Material).count(),
            "vendors": db.query(models.Vendor).count(),
            "purchase_orders": db.query(models.PurchaseOrder).count()
        }
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching procurement logs: {str(e)}")
