# app/routers/qrcode.py
import io
from typing import Optional
import qrcode
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from app import models, database

router = APIRouter(prefix="/qrcode", tags=["QR Code"])


@router.get("/{po_id}", summary="Generate QR image for a purchase order (text-embedded)")
def generate_qr(po_id: int, db: Session = Depends(database.get_db)):
    """
    Generates a PNG QR code that contains the human-readable, multi-line
    details of the purchase order (project, vendor, material, payments, deliveries).
    This endpoint does NOT produce a URL; the QR encodes text directly.
    """

    try:
        po = (
            db.query(models.PurchaseOrder)
            .options(
                joinedload(models.PurchaseOrder.project),
                joinedload(models.PurchaseOrder.vendor),
                joinedload(models.PurchaseOrder.material),
                joinedload(models.PurchaseOrder.payments),
                joinedload(models.PurchaseOrder.deliveries),
            )
            .filter(models.PurchaseOrder.id == po_id)
            .first()
        )
    except Exception as e:
        # Database error (connection closed, etc.)
        raise HTTPException(status_code=500, detail=f"Database error while fetching PO: {e}")

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    # Friendly names (fall back to ID if relationship missing)
    project_name = po.project.name if getattr(po, "project", None) else f"Project ID {po.project_id}"
    vendor_name = po.vendor.name if getattr(po, "vendor", None) else f"Vendor ID {po.vendor_id}"
    material_name = po.material.name if getattr(po, "material", None) else f"Material ID {po.material_id}"
    order_date = po.order_date.isoformat() if getattr(po, "order_date", None) else "N/A"

    # Build multi-line human-readable text
    lines = [
        f"Purchase Order ID: {po.id}",
        f"Project: {project_name}",
        f"Vendor: {vendor_name}",
        f"Material: {material_name}",
        f"Quantity: {po.quantity}",
        f"Price: {po.price}",
        f"Status: {po.status}",
        f"Order Date: {order_date}",
        "",
        "Payments:",
    ]

    payments = getattr(po, "payments", None)
    if payments and len(payments) > 0:
        for p in payments:
            pd = p.payment_date.isoformat() if getattr(p, "payment_date", None) else "N/A"
            lines.append(f"- ID {p.id} | Amount: {p.amount} | Date: {pd} | Status: {p.status}")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("Deliveries:")

    deliveries = getattr(po, "deliveries", None)
    if deliveries and len(deliveries) > 0:
        for d in deliveries:
            dd = d.delivery_date.isoformat() if getattr(d, "delivery_date", None) else "N/A"
            lines.append(f"- ID {d.id} | Date: {dd} | Received: {d.received_quantity} | Status: {d.status}")
    else:
        lines.append("- None")

    qr_text = "\n".join(lines)

    # Create QR with reasonable error correction and size for multi-line text
    qr = qrcode.QRCode(
        version=None,  # automatic
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=4,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # stream image back
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    filename = f"qrcode_po_{po.id}.png"
    return StreamingResponse(
        buf,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
