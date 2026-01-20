"""
Invoice View - formats invoice data for API responses.

This is the View layer that handles how data is presented to the client.
"""
from models import Invoice
from typing import Dict, Any, List


class InvoiceView:
    """View for formatting invoice data as JSON responses."""
    
    @staticmethod
    def format_invoice(invoice: Invoice) -> Dict[str, Any]:
        """
        Format a single invoice model as a dictionary for JSON response.
        
        Args:
            invoice: Invoice model instance
            
        Returns:
            Dictionary representation of the invoice with items
        """
        if not invoice:
            return None
        
        return {
            "InvoiceId": invoice.InvoiceId,
            "VendorName": invoice.VendorName,
            "InvoiceDate": invoice.InvoiceDate,
            "BillingAddressRecipient": invoice.BillingAddressRecipient,
            "ShippingAddress": invoice.ShippingAddress,
            "SubTotal": invoice.SubTotal,
            "ShippingCost": invoice.ShippingCost,
            "InvoiceTotal": invoice.InvoiceTotal,
            "Items": [InvoiceView.format_item(item) for item in invoice.items]
        }
    
    @staticmethod
    def format_item(item) -> Dict[str, Any]:
        """
        Format an item model as a dictionary.
        
        Args:
            item: Item model instance
            
        Returns:
            Dictionary representation of the item
        """
        return {
            "Description": item.Description,
            "Name": item.Name,
            "Quantity": item.Quantity,
            "UnitPrice": item.UnitPrice,
            "Amount": item.Amount
        }
    
    @staticmethod
    def format_invoices(invoices: List[Invoice]) -> List[Dict[str, Any]]:
        """
        Format a list of invoice models as dictionaries.
        
        Args:
            invoices: List of Invoice model instances
            
        Returns:
            List of dictionary representations
        """
        return [InvoiceView.format_invoice(invoice) for invoice in invoices]
    
    @staticmethod
    def format_vendor_response(vendor_name: str, invoices: List[Invoice]) -> Dict[str, Any]:
        """
        Format response for vendor invoices endpoint.
        
        Args:
            vendor_name: Name of the vendor
            invoices: List of Invoice model instances
            
        Returns:
            Formatted response with vendor name, count, and invoices
        """
        return {
            "VendorName": vendor_name,
            "TotalInvoices": len(invoices),
            "invoices": InvoiceView.format_invoices(invoices)
        }
