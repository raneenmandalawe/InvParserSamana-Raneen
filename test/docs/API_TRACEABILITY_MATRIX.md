# API Traceability Matrix - InvParser Application

This document maps each of your **3 API endpoints** to their test cases.

## Summary

| Endpoint | Method | Tests | Status |
|----------|--------|-------|--------|
| `/extract` | POST | 4 | ✅ |
| `/invoice/{invoice_id}` | GET | 2 | ✅ |
| `/invoices/vendor/{vendor_name}` | GET | 3 | ✅ |
| Integration Tests | - | 1 | ✅ |
| **TOTAL** | - | **10** | **100%** |

---

## POST /extract

**Description:** Upload PDF invoice and extract data using OCI Document AI

| Test ID | Test Name | Scenario | Expected Result |
|---------|-----------|----------|-----------------|
| EXT-001 | `test_extract_success` | Upload valid PDF, confidence ≥0.9 | 200 OK, data extracted |
| EXT-002 | `test_extract_low_confidence` | Upload PDF, confidence <0.9 | 400 Bad Request |
| EXT-003 | `test_extract_service_unavailable` | OCI service fails | 503 Service Unavailable |
| EXT-004 | `test_extract_missing_file` | No file provided | 422 Unprocessable Entity |

**Test Class:** `TestExtractEndpoint`

**Success Response:**
```json
{
  "confidence": 0.95,
  "data": {
    "InvoiceId": "INV-12345",
    "VendorName": "Test Vendor Inc",
    "InvoiceTotal": "2500.00"
  },
  "dataConfidence": {...},
  "predictionTime": 0.5
}
```

**Error Response:**
```json
{
  "error": "Invalid document. Please upload a valid PDF invoice with high confidence."
}
```

---

## GET /invoice/{invoice_id}

**Description:** Retrieve a specific invoice by its ID

| Test ID | Test Name | Scenario | Expected Result |
|---------|-----------|----------|-----------------|
| INV-001 | `test_get_invoice_success` | Valid invoice ID | 200 OK, invoice details |
| INV-002 | `test_get_invoice_not_found` | Non-existent invoice ID | 404 Not Found |

**Test Class:** `TestGetInvoiceEndpoint`

**Success Response:**
```json
{
  "invoice_id": "INV-001",
  "vendor_name": "Test Vendor",
  "invoice_date": "2024-01-15",
  "invoice_total": 1000.00,
  "confidence": 0.95
}
```

**Error Response:**
```json
{
  "error": "Invoice not found"
}
```

---

## GET /invoices/vendor/{vendor_name}

**Description:** Retrieve all invoices for a specific vendor

| Test ID | Test Name | Scenario | Expected Result |
|---------|-----------|----------|-----------------|
| VEN-001 | `test_get_invoices_by_vendor_success` | Vendor with invoices | 200 OK, list of invoices |
| VEN-002 | `test_get_invoices_by_vendor_empty` | Vendor with no invoices | 200 OK, empty list |
| VEN-003 | `test_get_invoices_by_vendor_with_spaces` | Vendor name has spaces | 200 OK, URL encoding handled |

**Test Class:** `TestGetInvoicesByVendorEndpoint`

**Success Response:**
```json
{
  "VendorName": "Vendor A",
  "TotalInvoices": 2,
  "invoices": [
    {
      "invoice_id": "INV-001",
      "vendor_name": "Vendor A",
      "invoice_date": "2024-01-15",
      "invoice_total": 1000.00
    },
    {
      "invoice_id": "INV-002",
      "vendor_name": "Vendor A",
      "invoice_date": "2024-01-20",
      "invoice_total": 1500.00
    }
  ]
}
```

---

## Integration Tests

**Description:** Complete workflows and data persistence

| Test ID | Test Name | Scenario | Expected Result |
|---------|-----------|----------|-----------------|
| INT-001 | `test_extract_and_retrieve_workflow` | Extract then retrieve invoice | Both operations succeed |

**Test Class:** `TestIntegration`

---

## HTTP Status Codes

| Code | Usage | Endpoints |
|------|-------|-----------|
| 200 | Success | GET endpoints, POST /extract |
| 400 | Low confidence | POST /extract |
| 404 | Not found | GET /invoice/{id} |
| 422 | Invalid request | POST /extract (missing file) |
| 503 | Service unavailable | POST /extract (OCI failure) |

---

## Test Coverage by Type

| Type | Count | % |
|------|-------|---|
| Success scenarios | 4 | 40% |
| Error scenarios | 4 | 40% |
| Edge cases | 1 | 10% |
| Integration | 1 | 10% |

---

## Mocking Strategy

**What's Mocked:**
- `app.doc_client` - The OCI Document AI client instance

**What's NOT Mocked:**
- Database operations (uses real SQLite)
- FastAPI routing
- Request/response handling

**Mock Decorator:**
```python
@patch('app.doc_client')
def test_extract_success(self, mock_doc_client):
    # Test implementation
```

---

## Database Schema Expectations

Tests expect these columns in the `invoices` table:
- `invoice_id` (TEXT, primary key)
- `vendor_name` (TEXT)
- `invoice_date` (TEXT)
- `invoice_total` (REAL)
- `confidence` (REAL)
- `data_confidence` (TEXT - JSON string)
- `prediction_time` (REAL)

---

## Running Tests

### All Tests
```bash
pytest test/test_api_integration.py -v
```

### Specific Test Class
```bash
# Just extraction tests
pytest test/test_api_integration.py::TestExtractEndpoint -v

# Just retrieval tests
pytest test/test_api_integration.py::TestGetInvoiceEndpoint -v

# Just vendor tests
pytest test/test_api_integration.py::TestGetInvoicesByVendorEndpoint -v
```

### With Coverage
```bash
pytest test/ --cov=app --cov=db_util --cov-report=html
```

---

## Success Criteria ✅

- [x] All 3 endpoints have tests
- [x] Success and failure scenarios covered
- [x] Error codes verified
- [x] Response structures validated
- [x] Integration workflow tested
- [x] Database persistence verified
- [x] OCI service mocked

---

## Last Updated
- **Date**: 2026-01-06
- **Version**: 1.0
- **Total Endpoints**: 3
- **Total Tests**: 10
- **Coverage**: 100%
