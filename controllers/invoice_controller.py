"""
Invoice Controller - handles CRUD operations for invoices.

This is the Controller layer that manages database operations
for Invoice, Item, and Confidence entities.
"""
from sqlalchemy.orm import Session
from models import Invoice, Item, Confidence
from typing import Optional, List, Dict, Any


class InvoiceController:
    """Controller for managing invoice database operations."""
    
    @staticmethod
    def create(db: Session, invoice_data: Dict[str, Any], confidence_data: Dict[str, Any]) -> Optional[str]:
        """
        Create or update an invoice with items and confidences.
        
        Args:
            db: Database session
            invoice_data: Dictionary containing invoice fields and items
            confidence_data: Dictionary containing confidence scores
            
        Returns:
            Invoice ID if successful, None otherwise
        """
        try:
            invoice_id = invoice_data.get("InvoiceId")
            
            print(f"DEBUG controller: invoice_id = {invoice_id}")
            
            if not invoice_id:
                print("DEBUG controller: No invoice_id found in data!")
                return None
            
            # Check if invoice exists
            existing_invoice = db.query(Invoice).filter_by(InvoiceId=invoice_id).first()
            
            if existing_invoice:
                # Update existing invoice
                existing_invoice.VendorName = invoice_data.get("VendorName")
                existing_invoice.InvoiceDate = invoice_data.get("InvoiceDate")
                existing_invoice.BillingAddressRecipient = invoice_data.get("BillingAddressRecipient")
                existing_invoice.ShippingAddress = invoice_data.get("ShippingAddress")
                existing_invoice.SubTotal = invoice_data.get("SubTotal")
                existing_invoice.ShippingCost = invoice_data.get("ShippingCost")
                existing_invoice.InvoiceTotal = invoice_data.get("InvoiceTotal")
                print("DEBUG controller: Invoice updated")
            else:
                # Create new invoice
                invoice = Invoice(
                    InvoiceId=invoice_id,
                    VendorName=invoice_data.get("VendorName"),
                    InvoiceDate=invoice_data.get("InvoiceDate"),
                    BillingAddressRecipient=invoice_data.get("BillingAddressRecipient"),
                    ShippingAddress=invoice_data.get("ShippingAddress"),
                    SubTotal=invoice_data.get("SubTotal"),
                    ShippingCost=invoice_data.get("ShippingCost"),
                    InvoiceTotal=invoice_data.get("InvoiceTotal")
                )
                db.add(invoice)
                print("DEBUG controller: Invoice created")
            
            # Handle confidences
            existing_confidence = db.query(Confidence).filter_by(InvoiceId=invoice_id).first()
            
            if existing_confidence:
                # Update existing confidence
                existing_confidence.VendorName = confidence_data.get("VendorName")
                existing_confidence.InvoiceDate = confidence_data.get("InvoiceDate")
                existing_confidence.BillingAddressRecipient = confidence_data.get("BillingAddressRecipient")
                existing_confidence.ShippingAddress = confidence_data.get("ShippingAddress")
                existing_confidence.SubTotal = confidence_data.get("SubTotal")
                existing_confidence.ShippingCost = confidence_data.get("ShippingCost")
                existing_confidence.InvoiceTotal = confidence_data.get("InvoiceTotal")
            else:
                # Create new confidence
                confidence = Confidence(
                    InvoiceId=invoice_id,
                    VendorName=confidence_data.get("VendorName"),
                    InvoiceDate=confidence_data.get("InvoiceDate"),
                    BillingAddressRecipient=confidence_data.get("BillingAddressRecipient"),
                    ShippingAddress=confidence_data.get("ShippingAddress"),
                    SubTotal=confidence_data.get("SubTotal"),
                    ShippingCost=confidence_data.get("ShippingCost"),
                    InvoiceTotal=confidence_data.get("InvoiceTotal")
                )
                db.add(confidence)
            
            print("DEBUG controller: Confidences saved")
            
            # Delete old items
            db.query(Item).filter_by(InvoiceId=invoice_id).delete()
            
            # Add new items
            items = invoice_data.get("Items", [])
            print(f"DEBUG controller: Number of items to insert: {len(items)}")
            
            for item_data in items:
                item = Item(
                    InvoiceId=invoice_id,
                    Description=item_data.get("Description"),
                    Name=item_data.get("Name"),
                    Quantity=item_data.get("Quantity"),
                    UnitPrice=item_data.get("UnitPrice"),
                    Amount=item_data.get("Amount")
                )
                db.add(item)
            
            print("DEBUG controller: Items inserted")
            
            # Commit all changes
            db.commit()
            
            print(f"DEBUG controller: Successfully saved invoice {invoice_id}")
            return invoice_id
            
        except Exception as e:
            print(f"DEBUG controller ERROR: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
            raise
    
    @staticmethod
    def get_by_id(db: Session, invoice_id: str) -> Optional[Invoice]:
        """
        Retrieve an invoice by ID.
        
        Args:
            db: Database session
            invoice_id: The invoice ID to retrieve
            
        Returns:
            Invoice model instance or None
        """
        return db.query(Invoice).filter_by(InvoiceId=invoice_id).first()
    
    @staticmethod
    def get_by_vendor(db: Session, vendor_name: str) -> List[Invoice]:
        """
        Retrieve all invoices for a specific vendor.
        
        Args:
            db: Database session
            vendor_name: The vendor name to search for
            
        Returns:
            List of Invoice model instances
        """
        return db.query(Invoice).filter_by(VendorName=vendor_name).all()
    
    @staticmethod
    def delete(db: Session, invoice_id: str) -> bool:
        """
        Delete an invoice and its associated items and confidences.
        
        Args:
            db: Database session
            invoice_id: The invoice ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            invoice = db.query(Invoice).filter_by(InvoiceId=invoice_id).first()
            
            if not invoice:
                return False
            
            # Cascade delete handles items and confidences
            db.delete(invoice)
            db.commit()
            
            return True
        except Exception as e:
            print(f"Error deleting invoice: {e}")
            db.rollback()
            return False
