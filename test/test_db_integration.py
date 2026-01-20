"""
Integration tests for database functionality using unittest.

Tests CRUD operations on Invoice and Item entities using SQLAlchemy ORM.
"""
import unittest
import os
from sqlalchemy.orm import Session

# Set test environment
os.environ["DB_BACKEND"] = "sqlite"

from db import SessionLocal, init_db, clean_db
from controllers import InvoiceController
from views import InvoiceView


class TestDatabaseIntegration(unittest.TestCase):
    """Test database CRUD operations using SQLAlchemy."""
    
    @classmethod
    def setUpClass(cls):
        """Set up database schema once for all tests."""
        init_db()
    
    def setUp(self):
        """Create a fresh database session before each test."""
        self.db: Session = SessionLocal()
    
    def tearDown(self):
        """Clean up database session after each test."""
        self.db.close()
        # Clean and recreate schema
        clean_db()
        init_db()
    
    def test_save_and_retrieve_invoice(self):
        """Test creating and retrieving an invoice."""
        # Arrange
        result = {
            "confidence": 0.95,
            "data": {
                "InvoiceId": "INV-001",
                "VendorName": "Test Vendor",
                "InvoiceDate": "2026-01-19",
                "BillingAddressRecipient": "John Doe",
                "ShippingAddress": "123 Main St",
                "SubTotal": 100.0,
                "ShippingCost": 10.0,
                "InvoiceTotal": 110.0,
                "Items": [
                    {
                        "Description": "Product A",
                        "Name": "A",
                        "Quantity": 2.0,
                        "UnitPrice": 50.0,
                        "Amount": 100.0,
                    }
                ],
            },
            "dataConfidence": {
                "VendorName": 0.95,
                "InvoiceDate": 0.99,
            },
        }
        
        # Act
        invoice_id = InvoiceController.create(self.db, result["data"], result["dataConfidence"])
        retrieved_invoice = InvoiceController.get_by_id(self.db, "INV-001")
        retrieved = InvoiceView.format_invoice(retrieved_invoice)
        
        # Assert
        self.assertEqual(invoice_id, "INV-001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["VendorName"], "Test Vendor")
        self.assertEqual(retrieved["InvoiceTotal"], 110.0)
        self.assertEqual(len(retrieved["Items"]), 1)
        self.assertEqual(retrieved["Items"][0]["Name"], "A")
    
    def test_get_invoice_not_found(self):
        """Test retrieving non-existent invoice returns None."""
        invoice = InvoiceController.get_by_id(self.db, "DOES-NOT-EXIST")
        self.assertIsNone(invoice)
    
    def test_get_invoices_by_vendor(self):
        """Test retrieving all invoices for a vendor."""
        # Create invoices for two vendors
        result1 = {
            "data": {
                "InvoiceId": "INV-V1",
                "VendorName": "VendorA",
                "InvoiceTotal": 100.0,
                "Items": [],
            },
            "dataConfidence": {},
        }
        
        result2 = {
            "data": {
                "InvoiceId": "INV-V2",
                "VendorName": "VendorA",
                "InvoiceTotal": 200.0,
                "Items": [],
            },
            "dataConfidence": {},
        }
        
        result3 = {
            "data": {
                "InvoiceId": "INV-V3",
                "VendorName": "VendorB",
                "InvoiceTotal": 300.0,
                "Items": [],
            },
            "dataConfidence": {},
        }
        
        InvoiceController.create(self.db, result1["data"], result1["dataConfidence"])
        InvoiceController.create(self.db, result2["data"], result2["dataConfidence"])
        InvoiceController.create(self.db, result3["data"], result3["dataConfidence"])
        
        # Get invoices for VendorA
        invoice_models = InvoiceController.get_by_vendor(self.db, "VendorA")
        invoices = InvoiceView.format_invoices(invoice_models)
        
        self.assertEqual(len(invoices), 2)
        invoice_ids = {inv["InvoiceId"] for inv in invoices}
        self.assertEqual(invoice_ids, {"INV-V1", "INV-V2"})
    
    def test_get_invoices_by_vendor_empty(self):
        """Test getInvoiceController.gets for vendor with no invoices."""
        invoices = InvoiceController.get_by_vendor(self.db, "NonExistent")
        self.assertEqual(invoices, [])
    
    def test_update_invoice(self):
        """Test updating an existing invoice."""
        # Create initial invoice
        result = {
            "data": {
                "InvoiceId": "INV-UPD",
                "VendorName": "Old Vendor",
                "InvoiceTotal": 100.0,
                "Items": [{"Description": "Old", "Name": "O", "Quantity": 1, "UnitPrice": 100, "Amount": 100}],
            },
            "dataConfidence": {},
        }
        
        InvoiceController.create(self.db, result["data"], result["dataConfidence"])
        
        # Update invoice
        updated_result = {
            "data": {
                "InvoiceId": "INV-UPD",
                "VendorName": "New Vendor",
                "InvoiceTotal": 200.0,
                "Items": [{"Description": "New", "Name": "N", "Quantity": 2, "UnitPrice": 100, "Amount": 200}],
            },
            "dataConfidence": {},
        }
        
        InvoiceController.create(self.db, updated_result["data"], updated_result["dataConfidence"])
        
        # Verify update
        invoice_model = InvoiceController.get_by_id(self.db, "INV-UPD")
        invoice = InvoiceView.format_invoice(invoice_model)
        self.assertEqual(invoice["VendorName"], "New Vendor")
        self.assertEqual(invoice["InvoiceTotal"], 200.0)
        self.assertEqual(len(invoice["Items"]), 1)
        self.assertEqual(invoice["Items"][0]["Name"], "N")
    
    def test_delete_invoice(self):
        """Test deleting an invoice."""
        # Create invoice
        result = {
            "data": {
                "InvoiceId": "INV-DEL",
                "VendorName": "To Delete",
                "Items": [],
            },
            "dataConfidence": {},
        }
        InvoiceController.create(self.db, result["data"], result["dataConfidence"])
        self.assertIsNotNone(InvoiceController.get_by_id(self.db, "INV-DEL"))
        
        # Delete
        success = InvoiceController.delete(self.db, "INV-DEL")
        self.assertTrue(success)
        
        # Verify deletion
        self.assertIsNone(InvoiceController.get_by_id(self.db, "INV-DEL"))
    
    def test_save_invoice_with_multiple_items(self):
        """Test creating invoice with multiple line items."""
        result = {
            "data": {
                "InvoiceId": "INV-MULTI",
                "VendorName": "Multi Items Vendor",
                "InvoiceTotal": 350.0,
                "Items": [
                    {"Description": "Item 1", "Name": "I1", "Quantity": 2, "UnitPrice": 50, "Amount": 100},
                    {"Description": "Item 2", "Name": "I2", "Quantity": 1, "UnitPrice": 150, "Amount": 150},
                    {"Description": "Item 3", "Name": "I3", "Quantity": 5, "UnitPrice": 20, "Amount": 100},
                ],
            },
            "dataConfidence": {},
        }
        InvoiceController.create(self.db, result["data"], result["dataConfidence"])
        
        invoice_model = InvoiceController.get_by_id(self.db, "INV-MULTI")
        invoice = InvoiceView.format_invoice(invoice_model)
        self.assertEqual(len(invoice["Items"]), 3)
        self.assertEqual(invoice["InvoiceTotal"], 350.0)
    
    def test_save_invoice_without_id(self):
        """Test saving invoice without InvoiceId returns None."""
        result = {
            "data": {
                "VendorName": "No ID Vendor",
                "Items": [],
            },
            "dataConfidence": {},
        }
        invoice_id = InvoiceController.create(self.db, result["data"], result["dataConfidence"])
        self.assertIsNone(invoice_id)
    
    def test_delete_invoice_error_handling(self):
        """Test delete with database error handling."""
        # Try to delete non-existent invoice (tests error path)
        result = InvoiceController.delete(self.db, "NONEXISTENT-ID")
        self.assertFalse(result)
    
    def test_format_invoice_none(self):
        """Test formatting None invoice."""
        from views.invoice_view import InvoiceView
        result = InvoiceView.format_invoice(None)
        self.assertIsNone(result)
    
    def test_create_with_invalid_data_triggers_exception(self):
        """Test create method with data that triggers database exception."""
        from unittest.mock import patch
        
        # Mock db.add to raise an exception
        with patch.object(self.db, 'add') as mock_add:
            mock_add.side_effect = Exception("Simulated DB error")
            
            result = {
                "data": {
                    "InvoiceId": "ERR-001",
                    "VendorName": "Test",
                    "InvoiceTotal": 100.0,
                },
                "dataConfidence": {},
            }
            
            # Should raise exception from controller
            with self.assertRaises(Exception):
                InvoiceController.create(self.db, result["data"], result["dataConfidence"])
    
    def test_delete_with_db_exception(self):
        """Test delete method when database operation fails."""
        from unittest.mock import patch
        
        # Create an invoice first
        result = {
            "data": {
                "InvoiceId": "DEL-ERR-001",
                "VendorName": "Test",
                "InvoiceTotal": 100.0,
            },
            "dataConfidence": {},
        }
        InvoiceController.create(self.db, result["data"], result["dataConfidence"])
        
        # Mock db.delete to raise an exception
        with patch.object(self.db, 'delete') as mock_delete:
            mock_delete.side_effect = Exception("Simulated DB delete error")
            
            # Should return False when exception occurs
            result = InvoiceController.delete(self.db, "DEL-ERR-001")
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
