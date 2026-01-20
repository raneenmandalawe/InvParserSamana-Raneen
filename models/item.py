"""Item model - represents the items table (invoice line items)."""
from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from db import Base


class Item(Base):
    """
    Model for items table.
    
    Represents a line item on an invoice.
    """
    __tablename__ = 'items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    InvoiceId = Column(String, ForeignKey('invoices.InvoiceId'))
    Description = Column(String)
    Name = Column(String)
    Quantity = Column(Float)
    UnitPrice = Column(Float)
    Amount = Column(Float)
    
    # Relationship
    invoice = relationship("Invoice", back_populates="items")
