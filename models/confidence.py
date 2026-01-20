"""Confidence model - stores confidence scores for invoice fields."""
from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from db import Base


class Confidence(Base):
    """
    Model for confidences table.
    
    Stores confidence scores for each extracted field in an invoice.
    """
    __tablename__ = 'confidences'
    
    InvoiceId = Column(String, ForeignKey('invoices.InvoiceId'), primary_key=True)
    VendorName = Column(Float)
    InvoiceDate = Column(Float)
    BillingAddressRecipient = Column(Float)
    ShippingAddress = Column(Float)
    SubTotal = Column(Float)
    ShippingCost = Column(Float)
    InvoiceTotal = Column(Float)
    
    # Relationship
    invoice = relationship("Invoice", back_populates="confidences")
