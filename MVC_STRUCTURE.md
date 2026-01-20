# MVC Refactoring Summary

## Overview
Successfully refactored the InvParser application to follow the **Model-View-Controller (MVC)** pattern using SQLAlchemy ORM with support for both SQLite and PostgreSQL databases.

## Folder Structure

```
InvParserSamana-Raneen/
├── models/                    # Model Layer (Database Entities)
│   ├── __init__.py           # Exports Base, Invoice, Item, Confidence
│   ├── invoice.py            # Invoice SQLAlchemy model
│   ├── item.py               # Item SQLAlchemy model
│   └── confidence.py         # Confidence SQLAlchemy model
├── controllers/               # Controller Layer (Business Logic)
│   ├── __init__.py           # Exports InvoiceController
│   └── invoice_controller.py # CRUD operations for invoices
├── views/                     # View Layer (Response Formatting)
│   ├── __init__.py           # Exports InvoiceView
│   └── invoice_view.py       # JSON response formatters
├── db.py                      # Database connection & session management
├── app.py                     # FastAPI application (API endpoints)
├── test/
│   ├── test_db_integration.py # Database CRUD tests (unittest)
│   └── test_api_integration.py # API endpoint tests (unittest)
└── requirements.txt           # Dependencies including SQLAlchemy
```

## MVC Components

### 1. Models (models/)
SQLAlchemy ORM entities representing database tables:

- **Invoice** ([models/invoice.py](models/invoice.py))
  - Fields: `invoice_id`, `vendor_name`, `invoice_date`, `invoice_total`, `due_date`, `created_at`, `updated_at`
  - Relationships: One-to-many with `Item`, one-to-one with `Confidence`
  - Cascade delete: Deleting an invoice removes all items and confidence records

- **Item** ([models/item.py](models/item.py))
  - Fields: `id`, `invoice_id`, `description`, `quantity`, `unit_price`, `amount`
  - Foreign key to `Invoice`

- **Confidence** ([models/confidence.py](models/confidence.py))
  - Fields: `invoice_id`, confidence scores for each extracted field
  - One-to-one relationship with `Invoice`

### 2. Controllers (controllers/)
Business logic and CRUD operations:

- **InvoiceController** ([controllers/invoice_controller.py](controllers/invoice_controller.py))
  - `create(db, data, confidence_data)` - Create or update invoice with items and confidence
  - `get_by_id(db, invoice_id)` - Retrieve invoice by ID
  - `get_by_vendor(db, vendor_name)` - Get all invoices for a vendor
  - `delete(db, invoice_id)` - Delete invoice and cascade to items/confidence

All methods are static and accept a `Session` parameter for database operations.

### 3. Views (views/)
Response formatting layer:

- **InvoiceView** ([views/invoice_view.py](views/invoice_view.py))
  - `format_invoice(invoice)` - Convert Invoice model to JSON dict
  - `format_item(item)` - Convert Item model to JSON dict
  - `format_invoices(invoices)` - Format list of invoices
  - `format_vendor_response(vendor_name, invoices)` - Format vendor summary response

### 4. Database Layer (db.py)
Manages database connections and sessions:

- Supports **SQLite** (default) and **PostgreSQL** via `DB_BACKEND` environment variable
- Connection pooling with SQLAlchemy
- Session factory with `get_db()` dependency for FastAPI
- Database initialization with `init_db()`

**Environment Variables:**
```bash
# SQLite (default)
DB_BACKEND=sqlite

# PostgreSQL
DB_BACKEND=postgres
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=predictions
```

## API Endpoints (app.py)

All endpoints now use the MVC pattern:

| Endpoint | Method | Controller | View |
|----------|--------|------------|------|
| `/extract` | POST | `InvoiceController.create()` | `InvoiceView.format_invoice()` |
| `/invoices/{invoice_id}` | GET | `InvoiceController.get_by_id()` | `InvoiceView.format_invoice()` |
| `/invoices/{invoice_id}` | DELETE | `InvoiceController.delete()` | Direct response |
| `/invoices/vendor/{vendor_name}` | GET | `InvoiceController.get_by_vendor()` | `InvoiceView.format_vendor_response()` |

Example flow for `/extract` endpoint:
```python
@app.post("/extract")
async def extract_endpoint(file: UploadFile, db: Session = Depends(get_db)):
    # 1. Extract data using OCI
    result = oci_client.extract_invoice(file_content)
    
    # 2. Controller: Save to database
    invoice_id = InvoiceController.create(db, result["data"], result["dataConfidence"])
    
    # 3. Controller: Retrieve saved invoice
    invoice = InvoiceController.get_by_id(db, invoice_id)
    
    # 4. View: Format response
    return InvoiceView.format_invoice(invoice)
```

## Testing

Converted all tests to **unittest** framework:

### Database Tests (test/test_db_integration.py)
- ✅ `test_save_and_retrieve_invoice` - Create and retrieve with items
- ✅ `test_save_invoice_with_multiple_items` - Multiple line items
- ✅ `test_save_invoice_without_id` - Validation
- ✅ `test_get_invoice_not_found` - Not found handling
- ✅ `test_get_invoices_by_vendor` - Vendor queries
- ✅ `test_get_invoices_by_vendor_empty` - Empty results
- ✅ `test_update_invoice` - Update existing invoice
- ✅ `test_delete_invoice` - Cascade delete

### API Tests (test/test_api_integration.py)
- ✅ `test_extract_success_saves_to_db` - Successful extraction
- ✅ `test_extract_low_confidence_returns_400` - Low confidence handling
- ✅ `test_extract_oci_failure_returns_503` - Service failure
- ✅ `test_get_invoice_found` - GET existing invoice
- ✅ `test_get_invoice_not_found` - GET non-existent invoice
- ✅ `test_get_invoices_by_vendor` - GET by vendor
- ✅ `test_get_invoices_by_vendor_empty` - GET empty vendor results

**Run all tests:**
```bash
python3 -m unittest discover -s test -p "test_*.py" -v
```

## Key Benefits

1. **Separation of Concerns**: Clear separation between data (models), logic (controllers), and presentation (views)
2. **No Raw SQL**: All database operations use SQLAlchemy ORM
3. **Database Agnostic**: Easy switching between SQLite and PostgreSQL
4. **Testability**: Each layer can be tested independently
5. **Maintainability**: Changes to one layer don't affect others
6. **Type Safety**: SQLAlchemy models provide type hints and validation

## Migration from Old Code

| Old Function | New MVC Components |
|--------------|-------------------|
| `save_inv_extraction(db, result)` | `InvoiceController.create(db, data, confidence)` |
| `get_invoice_by_id(db, id)` | `InvoiceController.get_by_id(db, id)` + `InvoiceView.format_invoice()` |
| `get_invoices_by_vendor(db, vendor)` | `InvoiceController.get_by_vendor(db, vendor)` + `InvoiceView.format_vendor_response()` |
| Raw SQL queries | SQLAlchemy ORM queries |

## Dependencies

Added to requirements.txt:
```
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0  # PostgreSQL adapter
```

## Test Results

```
Ran 15 tests in 0.324s
OK
```

All tests passing ✅
