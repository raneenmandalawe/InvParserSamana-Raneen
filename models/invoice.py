"""Invoice model - represents the invoices table."""
from sqlalchemy import Column, String, Float
from sqlalchemy.orm import relationship
from db import Base


class Invoice(Base):
    """
    Model for invoices table.
    
    Represents an invoice entity with vendor information and totals.
    """
    __tablename__ = 'invoices'
    
    InvoiceId = Column(String, primary_key=True)
    VendorName = Column(String)
    InvoiceDate = Column(String)
    BillingAddressRecipient = Column(String)
    ShippingAddress = Column(String)
    SubTotal = Column(Float)
    ShippingCost = Column(Float)
    InvoiceTotal = Column(Float)
    
    # Relationships
    confidences = relationship("Confidence", back_populates="invoice", cascade="all, delete-orphan")
    items = relationship("Item", back_populates="invoice", cascade="all, delete-orphan")
