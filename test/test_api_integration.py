"""
API integration tests using unittest with real database.

Tests FastAPI endpoints with actual SQLite database operations.
"""
import unittest
import os
from types import SimpleNamespace
from unittest.mock import patch
from fastapi.testclient import TestClient

# Set test environment
os.environ["DB_BACKEND"] = "sqlite"

from db import init_db, clean_db
import importlib
import sys


def _make_field(name, value, confidence=0.99):
    """Helper to create a mock OCI field."""
    return SimpleNamespace(
        field_label=SimpleNamespace(name=name, confidence=confidence),
        field_value=SimpleNamespace(value=value, items=None),
    )


def _make_item_field(name, value):
    """Helper to create a mock OCI item field."""
    return SimpleNamespace(
        field_label=SimpleNamespace(name=name, confidence=0.99),
        field_value=SimpleNamespace(value=value),
    )


def _make_items_field(items_list):
    """Helper to create a mock OCI Items field structure."""
    item_objs = []
    for item in items_list:
        item_field_objs = []
        for k, v in item.items():
            item_field_objs.append(_make_item_field(k, v))
        item_objs.append(
            SimpleNamespace(field_value=SimpleNamespace(items=item_field_objs))
        )
    return SimpleNamespace(
        field_label=SimpleNamespace(name="Items", confidence=0.99),
        field_value=SimpleNamespace(items=item_objs),
    )


def build_oci_response(invoice_confidence=0.95, fields=None, items=None):
    """Build a mock OCI response."""
    if fields is None:
        fields = {}
    if items is None:
        items = []
    
    document_fields = []
    for k, v in fields.items():
        document_fields.append(_make_field(k, v, confidence=0.97))
    document_fields.append(_make_items_field(items))
    
    page = SimpleNamespace(document_fields=document_fields)
    detected_types = [
        SimpleNamespace(document_type="INVOICE", confidence=invoice_confidence)
    ]
    data = SimpleNamespace(detected_document_types=detected_types, pages=[page])
    return SimpleNamespace(data=data)


class TestAPIIntegration(unittest.TestCase):
    """Test FastAPI endpoints with real database."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        # Initialize database
        init_db()
    
    def setUp(self):
        """Clean database and set up app with mocked OCI before each test."""
        clean_db()
        init_db()
        
        # Create patches
        self.config_patch = patch("oci.config.from_file", return_value={})
        self.client_patch = patch("oci.ai_document.AIServiceDocumentClient")
        
        # Start patches
        self.config_patch.start()
        self.mock_client_cls = self.client_patch.start()
        
        # Reload app with mocked OCI
        if "app" in sys.modules:
            del sys.modules["app"]
        
        import app
        importlib.reload(app)
        
        self.app_module = app
        self.client = TestClient(app.app)
    
    def tearDown(self):
        """Stop patches after each test."""
        self.config_patch.stop()
        self.client_patch.stop()
    
    def test_extract_success_saves_to_db(self):
        """Test successful extraction and DB save."""
        # Mock OCI response
        self.app_module.doc_client.analyze_document.return_value = build_oci_response(
            invoice_confidence=0.95,
            fields={
                "InvoiceId": "API-001",
                "VendorName": "ACME Corp",
                "InvoiceDate": "2026-01-19",
                "InvoiceTotal": 500.0,
            },
            items=[
                {"Description": "Product A", "Name": "A", "Quantity": 1, "UnitPrice": 500, "Amount": 500}
            ],
        )
        
        # Act
        response = self.client.post(
            "/extract",
            files={"file": ("invoice.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )
        
        # Assert API response
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertGreaterEqual(body["confidence"], 0.9)
        self.assertEqual(body["data"]["InvoiceId"], "API-001")
        self.assertEqual(body["data"]["VendorName"], "ACME Corp")
        self.assertEqual(len(body["data"]["Items"]), 1)
        
        # Assert DB save
        saved_response = self.client.get("/invoice/API-001")
        self.assertEqual(saved_response.status_code, 200)
        saved_invoice = saved_response.json()
        self.assertEqual(saved_invoice["VendorName"], "ACME Corp")
        self.assertEqual(len(saved_invoice["Items"]), 1)
    
    def test_extract_low_confidence_returns_400(self):
        """Test low confidence invoice returns 400 and doesn't save."""
        # Mock OCI response with low confidence
        self.app_module.doc_client.analyze_document.return_value = build_oci_response(
            invoice_confidence=0.50,
            fields={"InvoiceId": "LOW-001", "VendorName": "LowConf"},
            items=[],
        )
        
        # Act
        response = self.client.post(
            "/extract",
            files={"file": ("invoice.pdf", b"%PDF-1.4", "application/pdf")},
        )
        
        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertIn("invalid document", response.json()["error"].lower())
        
        # Verify not saved to DB
        get_response = self.client.get("/invoice/LOW-001")
        self.assertEqual(get_response.status_code, 404)
    
    def test_extract_oci_failure_returns_503(self):
        """Test OCI service failure returns 503."""
        # Mock OCI failure
        self.app_module.doc_client.analyze_document.side_effect = Exception("OCI down")
        
        # Act
        response = self.client.post(
            "/extract",
            files={"file": ("invoice.pdf", b"%PDF-1.4", "application/pdf")},
        )
        
        # Assert
        self.assertEqual(response.status_code, 503)
        self.assertIn("unavailable", response.json()["error"].lower())
    
    def test_get_invoice_found(self):
        """Test retrieving existing invoice."""
        # First create an invoice via extract
        self.app_module.doc_client.analyze_document.return_value = build_oci_response(
            invoice_confidence=0.95,
            fields={
                "InvoiceId": "GET-001",
                "VendorName": "TestVendor",
                "InvoiceTotal": 100.0,
            },
            items=[],
        )
        
        create_response = self.client.post(
            "/extract",
            files={"file": ("invoice.pdf", b"%PDF-1.4", "application/pdf")},
        )
        self.assertEqual(create_response.status_code, 200)
        
        # Now retrieve it
        response = self.client.get("/invoice/GET-001")
        
        self.assertEqual(response.status_code, 200)
        invoice = response.json()
        self.assertEqual(invoice["InvoiceId"], "GET-001")
        self.assertEqual(invoice["VendorName"], "TestVendor")
    
    def test_get_invoice_not_found(self):
        """Test retrieving non-existent invoice returns 404."""
        response = self.client.get("/invoice/DOES-NOT-EXIST")
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Invoice not found")
    
    def test_get_invoices_by_vendor(self):
        """Test retrieving all invoices for a vendor."""
        # Create two invoices for same vendor
        self.app_module.doc_client.analyze_document.return_value = build_oci_response(
            invoice_confidence=0.95,
            fields={"InvoiceId": "V-001", "VendorName": "ACME", "InvoiceTotal": 100.0},
            items=[],
        )
        self.client.post("/extract", files={"file": ("a.pdf", b"%PDF-1.4", "application/pdf")})
        
        self.app_module.doc_client.analyze_document.return_value = build_oci_response(
            invoice_confidence=0.95,
            fields={"InvoiceId": "V-002", "VendorName": "ACME", "InvoiceTotal": 200.0},
            items=[],
        )
        self.client.post("/extract", files={"file": ("b.pdf", b"%PDF-1.4", "application/pdf")})
        
        # Get invoices for vendor
        response = self.client.get("/invoices/vendor/ACME")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["VendorName"], "ACME")
        self.assertEqual(data["TotalInvoices"], 2)
        self.assertEqual(len(data["invoices"]), 2)
        
        invoice_ids = {inv["InvoiceId"] for inv in data["invoices"]}
        self.assertEqual(invoice_ids, {"V-001", "V-002"})
    
    def test_get_invoices_by_vendor_empty(self):
        """Test retrieving invoices for vendor with no invoices."""
        response = self.client.get("/invoices/vendor/NOVENDOR")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["VendorName"], "NOVENDOR")
        self.assertEqual(data["TotalInvoices"], 0)
        self.assertEqual(data["invoices"], [])
    
    def test_extract_with_save_exception(self):
        """Test extraction when save fails (covers app.py lines 101-102)."""
        # Mock OCI response
        self.app_module.doc_client.analyze_document.return_value = build_oci_response(
            invoice_confidence=0.95,
            fields={
                "InvoiceId": "EXC-001",
                "VendorName": "ExceptionVendor",
                "InvoiceTotal": 100.0,
            },
            items=[],
        )
        
        # Mock InvoiceController.create to raise exception
        with patch("app.InvoiceController.create") as mock_create:
            mock_create.side_effect = Exception("DB Error")
            
            response = self.client.post(
                "/extract",
                files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
            )
            
            # Should still return 200 with extraction result
            self.assertEqual(response.status_code, 200)
            self.assertIn("data", response.json())
            self.assertIn("InvoiceId", response.json()["data"])


if __name__ == "__main__":
    unittest.main()
