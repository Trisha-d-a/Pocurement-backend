# app/schemas.py
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

# ---------- Project ----------
class ProjectBase(BaseModel):
    name: str
    location: str

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Material ----------
class MaterialBase(BaseModel):
    name: str
    unit: str

class MaterialCreate(MaterialBase):
    pass

class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None

class Material(MaterialBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Vendor ----------
class VendorBase(BaseModel):
    name: str
    contact: str
    trust_score: Optional[float] = 0.0

class VendorCreate(VendorBase):
    pass

class VendorUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    trust_score: Optional[float] = None

class Vendor(VendorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- BOQ ----------
class BoqBase(BaseModel):
    project_id: int
    material_id: int
    quantity: float

class BoqCreate(BoqBase):
    pass

class Boq(BoqBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Quotation ----------
class QuotationBase(BaseModel):
    project_id: int
    material_id: int
    vendor_id: int
    price: float
    payment_terms: Optional[str] = None
    date: Optional[datetime] = None

class QuotationCreate(QuotationBase):
    pass

class Quotation(QuotationBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Purchase Order ----------
class PurchaseOrderBase(BaseModel):
    project_id: int
    vendor_id: int
    material_id: int
    quantity: int
    price: float
    order_date: Optional[datetime] = None
    status: Optional[str] = "Pending"

class PurchaseOrderCreate(PurchaseOrderBase):
    pass

class PurchaseOrder(PurchaseOrderBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Payment ----------
class PaymentBase(BaseModel):
    purchase_order_id: int
    amount: float
    payment_date: Optional[datetime] = None
    status: Optional[str] = "Pending"

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Delivery ----------
class DeliveryBase(BaseModel):
    purchase_order_id: int
    delivery_date: Optional[datetime] = None
    status: Optional[str] = "Pending"
    received_quantity: Optional[int] = 0

class DeliveryCreate(DeliveryBase):
    pass

class Delivery(DeliveryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- User ----------
class UserBase(BaseModel):
    username: str
    phone_number: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Auth / Login ----------
class LoginRequest(BaseModel):
    username: str
    password: str
