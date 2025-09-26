# app/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


# ---------- User ----------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=True)


# ---------- Project ----------
class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    location = Column(String, nullable=False)

    boq_items = relationship("BOQ", back_populates="project", cascade="all, delete-orphan")
    quotations = relationship("Quotation", back_populates="project", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="project", cascade="all, delete-orphan")


# ---------- Material ----------
class Material(Base):
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    unit = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    boq_items = relationship("BOQ", back_populates="material", cascade="all, delete-orphan")
    quotations = relationship("Quotation", back_populates="material", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="material", cascade="all, delete-orphan")


# ---------- Vendor ----------
class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    contact = Column(String, nullable=False)
    trust_score = Column(Float, default=0.0)

    quotations = relationship("Quotation", back_populates="vendor", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor", cascade="all, delete-orphan")


# ---------- BOQ ----------
class BOQ(Base):
    __tablename__ = "boq"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Float, nullable=False)

    project = relationship("Project", back_populates="boq_items")
    material = relationship("Material", back_populates="boq_items")


# ---------- Quotation ----------
class Quotation(Base):
    __tablename__ = "quotations"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    price = Column(Float, nullable=False)
    payment_terms = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="quotations")
    material = relationship("Material", back_populates="quotations")
    vendor = relationship("Vendor", back_populates="quotations")


# ---------- Purchase Order ----------
class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Pending")

    project = relationship("Project", back_populates="purchase_orders")
    vendor = relationship("Vendor", back_populates="purchase_orders")
    material = relationship("Material", back_populates="purchase_orders")
    payments = relationship("Payment", back_populates="purchase_order", cascade="all, delete-orphan")
    deliveries = relationship("Delivery", back_populates="purchase_order", cascade="all, delete-orphan")


# ---------- Payment ----------
class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Pending")

    purchase_order = relationship("PurchaseOrder", back_populates="payments")


# ---------- Delivery ----------
class Delivery(Base):
    __tablename__ = "deliveries"
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    delivery_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Pending")
    received_quantity = Column(Integer, default=0)

    purchase_order = relationship("PurchaseOrder", back_populates="deliveries")
