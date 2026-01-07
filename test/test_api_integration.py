"""
Integration tests for InvParser API endpoints.

This module tests the 3 endpoints in your app.py:
- POST /extract - Invoice extraction with OCI Document AI
- GET /invoice/{invoice_id} - Get invoice by ID
- GET /invoices/vendor/{vendor_name} - Get invoices by vendor
"""

import unittest
import io
import sqlite3
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app import app
from db_util import init_db, clean_db

# Get database connection function
def get_db_connection():
    """Get database connection - compatible with your db_util.py structure."""
    import os
    db_path = os.getenv('DB_PATH', 'invoices.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


class TestExtractEndpoint(unittest.TestCase):
    """Tests for POST /extract endpoint."""
    
    def setUp(self):
        """Set up test database and client."""
        init_db()
        self.client = TestClient(app)
    
    def tearDown(self):
        """Clean up test database."""
        clean_db()
    
    @patch('app.doc_client')
    def test_extract_success(self, mock_doc_client):
        """Test successful invoice extraction with high confidence."""
        # Mock OCI response with high confidence
        mock_response = MagicMock()
        mock_response.data = MagicMock()
        
        # Mock document type - INVOICE with confidence > 0.9
        mock_doc_type = MagicMock()
        mock_doc_type.document_type = "INVOICE"
        mock_doc_type.confidence = 0.95
        mock_response.data.detected_document_types = [mock_doc_type]
        
        # Mock page with fields
        mock_page = MagicMock()
        
        # Create fields matching YOUR schema
        mock_field1 = MagicMock()
        mock_field1.field_label = MagicMock()
        mock_field1.field_label.name = "InvoiceId"
        mock_field1.field_label.confidence = 0.98
        mock_field1.field_value = MagicMock()
        mock_field1.field_value.value = "INV-12345"
        mock_field1.field_value.items = None
        
        mock_field2 = MagicMock()
        mock_field2.field_label = MagicMock()
        mock_field2.field_label.name = "VendorName"
        mock_field2.field_label.confidence = 0.97
        mock_field2.field_value = MagicMock()
        mock_field2.field_value.value = "Test Vendor Inc"
        mock_field2.field_value.items = None
        
        mock_field3 = MagicMock()
        mock_field3.field_label = MagicMock()
        mock_field3.field_label.name = "InvoiceTotal"
        mock_field3.field_label.confidence = 0.96
        mock_field3.field_value = MagicMock()
        mock_field3.field_value.value = "2500.00"
        mock_field3.field_value.items = None
        
        mock_page.document_fields = [mock_field1, mock_field2, mock_field3]
        mock_response.data.pages = [mock_page]
        
        mock_doc_client.analyze_document.return_value = mock_response
        
        # Create test PDF
        pdf_content = b"%PDF-1.4 test content"
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        # Test the endpoint
        response = self.client.post("/extract", files=files)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("confidence", result)
        self.assertIn("data", result)
        self.assertIn("dataConfidence", result)
        self.assertIn("predictionTime", result)
        
        self.assertGreaterEqual(result["confidence"], 0.9)
        self.assertEqual(result["data"]["InvoiceId"], "INV-12345")
        self.assertEqual(result["data"]["VendorName"], "Test Vendor Inc")
    
    @patch('app.doc_client')
    def test_extract_low_confidence(self, mock_doc_client):
        """Test extraction with confidence below 0.9 threshold."""
        # Mock OCI response with LOW confidence
        mock_response = MagicMock()
        mock_response.data = MagicMock()
        
        mock_doc_type = MagicMock()
        mock_doc_type.document_type = "INVOICE"
        mock_doc_type.confidence = 0.75  # Below threshold
        mock_response.data.detected_document_types = [mock_doc_type]
        
        mock_response.data.pages = []
        
        mock_doc_client.analyze_document.return_value = mock_response
        
        # Create test PDF
        pdf_content = b"%PDF-1.4 test content"
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        # Test the endpoint
        response = self.client.post("/extract", files=files)
        
        # Should return 400 for low confidence
        self.assertEqual(response.status_code, 400)
        result = response.json()
        self.assertIn("error", result)
        self.assertIn("Invalid document", result["error"])
    
    @patch('app.doc_client')
    def test_extract_service_unavailable(self, mock_doc_client):
        """Test extraction when OCI service fails."""
        # Mock OCI service exception
        mock_doc_client.analyze_document.side_effect = Exception("Service error")
        
        # Create test PDF
        pdf_content = b"%PDF-1.4 test content"
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        # Test the endpoint
        response = self.client.post("/extract", files=files)
        
        # Should return 503 for service unavailable
        self.assertEqual(response.status_code, 503)
        result = response.json()
        self.assertIn("error", result)
        self.assertIn("currently unavailable", result["error"])
    
    def test_extract_missing_file(self):
        """Test extraction without providing a file."""
        response = self.client.post("/extract")
        
        # Should return 422 for missing required field
        self.assertEqual(response.status_code, 422)


class TestGetInvoiceEndpoint(unittest.TestCase):
    """Tests for GET /invoice/{invoice_id} endpoint."""
    
    def setUp(self):
        """Set up test database with sample data."""
        init_db()
        self.client = TestClient(app)
        
        # Insert test invoice using YOUR schema (PascalCase columns)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO invoices (InvoiceId, VendorName, InvoiceDate, InvoiceTotal)
               VALUES (?, ?, ?, ?)""",
            ("INV-001", "Test Vendor", "2024-01-15", 1000.00)
        )
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up test database."""
        clean_db()
    
    def test_get_invoice_success(self):
        """Test successful invoice retrieval."""
        response = self.client.get("/invoice/INV-001")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Your app returns the data, verify it exists
        self.assertIsInstance(result, dict)
        # The exact structure depends on your get_invoice_by_id implementation
    
    def test_get_invoice_not_found(self):
        """Test retrieval of non-existent invoice."""
        response = self.client.get("/invoice/INV-999")
        
        self.assertEqual(response.status_code, 404)
        result = response.json()
        self.assertIn("error", result)
        self.assertIn("Invoice not found", result["error"])


class TestGetInvoicesByVendorEndpoint(unittest.TestCase):
    """Tests for GET /invoices/vendor/{vendor_name} endpoint."""
    
    def setUp(self):
        """Set up test database with sample data."""
        init_db()
        self.client = TestClient(app)
        
        # Insert test invoices using YOUR schema
        conn = get_db_connection()
        cursor = conn.cursor()
        
        test_invoices = [
            ("INV-001", "Vendor A", "2024-01-15", 1000.00),
            ("INV-002", "Vendor A", "2024-01-20", 1500.00),
            ("INV-003", "Vendor B", "2024-01-25", 2000.00),
        ]
        
        for inv_id, vendor, date, total in test_invoices:
            cursor.execute(
                """INSERT INTO invoices (InvoiceId, VendorName, InvoiceDate, InvoiceTotal)
                   VALUES (?, ?, ?, ?)""",
                (inv_id, vendor, date, total)
            )
        
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up test database."""
        clean_db()
    
    def test_get_invoices_by_vendor_success(self):
        """Test successful retrieval of invoices by vendor."""
        response = self.client.get("/invoices/vendor/Vendor A")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("VendorName", result)
        self.assertIn("TotalInvoices", result)
        self.assertIn("invoices", result)
        
        self.assertEqual(result["VendorName"], "Vendor A")
        self.assertEqual(result["TotalInvoices"], 2)
        self.assertEqual(len(result["invoices"]), 2)
    
    def test_get_invoices_by_vendor_empty(self):
        """Test retrieval for vendor with no invoices."""
        response = self.client.get("/invoices/vendor/Vendor C")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertEqual(result["VendorName"], "Vendor C")
        self.assertEqual(result["TotalInvoices"], 0)
        self.assertEqual(len(result["invoices"]), 0)
    
    def test_get_invoices_by_vendor_with_spaces(self):
        """Test vendor name with spaces (URL encoding)."""
        # Insert vendor with spaces
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO invoices (InvoiceId, VendorName, InvoiceDate, InvoiceTotal)
               VALUES (?, ?, ?, ?)""",
            ("INV-004", "ABC Company Inc", "2024-01-30", 3000.00)
        )
        conn.commit()
        conn.close()
        
        # Test with URL-encoded space
        response = self.client.get("/invoices/vendor/ABC%20Company%20Inc")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["TotalInvoices"], 1)
    
    def test_get_invoices_by_vendor_with_items(self):
        """Test retrieval of invoices that include line items."""
        # Insert invoice with items
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert invoice
        cursor.execute(
            """INSERT INTO invoices (InvoiceId, VendorName, InvoiceDate, InvoiceTotal)
               VALUES (?, ?, ?, ?)""",
            ("INV-005", "Vendor With Items", "2024-02-01", 5000.00)
        )
        
        # Insert items for this invoice
        items_data = [
            ("INV-005", "Product A", "Item A", 2, 100.00, 200.00),
            ("INV-005", "Product B", "Item B", 3, 150.00, 450.00),
        ]
        
        for item in items_data:
            cursor.execute(
                """INSERT INTO items (InvoiceId, Description, Name, Quantity, UnitPrice, Amount)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                item
            )
        
        conn.commit()
        conn.close()
        
        # Test the endpoint
        response = self.client.get("/invoices/vendor/Vendor With Items")
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertEqual(result["TotalInvoices"], 1)
        self.assertEqual(len(result["invoices"]), 1)
        
        # Verify items are included
        invoice = result["invoices"][0]
        self.assertIn("Items", invoice)
        self.assertEqual(len(invoice["Items"]), 2)
        
        # Verify item details
        items = invoice["Items"]
        self.assertEqual(items[0]["Description"], "Product A")
        self.assertEqual(items[0]["Quantity"], 2)
        self.assertEqual(items[1]["Description"], "Product B")
        self.assertEqual(items[1]["Quantity"], 3)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows."""
    
    def setUp(self):
        """Set up test database and client."""
        init_db()
        self.client = TestClient(app)
    
    def tearDown(self):
        """Clean up test database."""
        clean_db()
    
    @patch('app.doc_client')
    def test_extract_and_retrieve_workflow(self, mock_doc_client):
        """Test complete workflow: extract invoice then retrieve it."""
        # Mock OCI response
        mock_response = MagicMock()
        mock_response.data = MagicMock()
        
        mock_doc_type = MagicMock()
        mock_doc_type.document_type = "INVOICE"
        mock_doc_type.confidence = 0.95
        mock_response.data.detected_document_types = [mock_doc_type]
        
        mock_page = MagicMock()
        
        mock_field1 = MagicMock()
        mock_field1.field_label = MagicMock()
        mock_field1.field_label.name = "InvoiceId"
        mock_field1.field_label.confidence = 0.98
        mock_field1.field_value = MagicMock()
        mock_field1.field_value.value = "INV-WORKFLOW-001"
        mock_field1.field_value.items = None
        
        mock_field2 = MagicMock()
        mock_field2.field_label = MagicMock()
        mock_field2.field_label.name = "VendorName"
        mock_field2.field_label.confidence = 0.97
        mock_field2.field_value = MagicMock()
        mock_field2.field_value.value = "Workflow Vendor"
        mock_field2.field_value.items = None
        
        mock_page.document_fields = [mock_field1, mock_field2]
        mock_response.data.pages = [mock_page]
        
        mock_doc_client.analyze_document.return_value = mock_response
        
        # Step 1: Extract invoice
        pdf_content = b"%PDF-1.4 test content"
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        extract_response = self.client.post("/extract", files=files)
        self.assertEqual(extract_response.status_code, 200)
        
        # Step 2: Retrieve the invoice
        get_response = self.client.get("/invoice/INV-WORKFLOW-001")
        self.assertEqual(get_response.status_code, 200)
        
        # Verify it's a valid response
        result = get_response.json()
        self.assertIsInstance(result, dict)


if __name__ == '__main__':
    unittest.main(verbosity=2)
