# InvParser - MVC Refactor Documentation

## Overview

This project has been successfully refactored to use the **Model-View-Controller (MVC)** pattern with **SQLAlchemy ORM**, replacing all raw SQL queries with Python classes and ORM operations.

## Architecture

### Models (`models.py`)
Defines database schema using SQLAlchemy ORM:

- **Invoice**: Main invoice entity with fields like InvoiceId, VendorName, InvoiceDate, etc.
- **Confidence**: Stores confidence scores for each field in the invoice
- **Item**: Represents line items in an invoice

Each model:
- Inherits from SQLAlchemy's `Base` class
- Uses `Column` to define database fields
- Defines relationships between tables
- Includes `to_dict()` method for JSON serialization

### Database Connection (`db.py`)
Manages database connections and sessions:

- **Database Agnostic**: Supports both SQLite and PostgreSQL
- **Environment-Based Configuration**: Switch databases using `DB_BACKEND` environment variable
- **Session Management**: Provides `get_db()` dependency for FastAPI
- **Schema Management**: `init_db()` creates tables, `clean_db()` drops tables

#### Switching Databases

```bash
# Use SQLite (default)
export DB_BACKEND=sqlite

# Use PostgreSQL
export DB_BACKEND=postgres
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=predictions
export POSTGRES_USER=user
export POSTGRES_PASSWORD=pass
```

### Queries/Controller (`queries.py`)
Handles all database operations (CRUD):

- **save_inv_extraction()**: Save or update invoice with items and confidences
- **get_invoice_by_id()**: Retrieve invoice by ID
- **get_invoices_by_vendor()**: Get all invoices for a vendor
- **delete_invoice()**: Delete invoice and related data

All functions use SQLAlchemy ORM instead of raw SQL.

### View/API (`app.py`)
FastAPI endpoints that use dependency injection:

```python
@app.get("/invoice/{invoice_id}")
async def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    invoice = get_invoice_by_id(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice
```

## Benefits of This Architecture

1. **Separation of Concerns**: Data models, business logic, and API endpoints are separated
2. **Type Safety**: Python classes provide IDE autocomplete and type checking
3. **Database Agnostic**: Easy to switch between SQLite and PostgreSQL
4. **Maintainable**: No raw SQL strings scattered throughout the code
5. **Testable**: Each layer can be tested independently

## Testing

Tests have been converted from pytest to **unittest** framework.

### Running Tests

```bash
# Set database backend
export DB_BACKEND=sqlite

# Run all tests
python3 -m unittest test.test_app -v

# Run specific test class
python3 -m unittest test.test_app.TestDatabaseQueries -v

# Run specific test
python3 -m unittest test.test_app.TestDatabaseQueries.test_save_and_get_invoice -v
```

### Test Coverage

The test suite includes:

1. **Database Query Tests** (`TestDatabaseQueries`):
   - Save and retrieve invoices
   - Update existing invoices
   - Query by vendor
   - Handle missing records

2. **API Endpoint Tests** (`TestAPIEndpoints`):
   - Invoice extraction with OCI
   - Low confidence handling
   - Error scenarios (OCI failures, DB failures)
   - GET endpoints for invoices

## Database Operations Comparison

### Before (Raw SQL)
```python
cursor.execute("""
    INSERT OR REPLACE INTO invoices 
    (InvoiceId, VendorName, InvoiceDate, ...)
    VALUES (?, ?, ?, ...)
""", (invoice_id, vendor_name, invoice_date, ...))
```

### After (SQLAlchemy ORM)
```python
invoice = Invoice(
    InvoiceId=invoice_id,
    VendorName=vendor_name,
    InvoiceDate=invoice_date,
    ...
)
db.add(invoice)
db.commit()
```

## File Structure

```
InvParserSamana-Raneen/
├── app.py                 # FastAPI application (View/Controller)
├── models.py              # SQLAlchemy models (Model)
├── db.py                  # Database connection management
├── queries.py             # Database queries (Controller)
├── requirements.txt       # Python dependencies
├── test/
│   └── test_app.py       # Unittest test suite
└── invoices.db           # SQLite database (auto-created)
```

## Testing with PostgreSQL

To test with PostgreSQL using Docker:

```bash
# 1. Start PostgreSQL container
docker run --rm \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=pass \
  -e POSTGRES_DB=predictions \
  -p 5432:5432 \
  postgres

# 2. Set environment variables
export DB_BACKEND=postgres
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=predictions
export POSTGRES_USER=user
export POSTGRES_PASSWORD=pass

# 3. Run the application
python3 app.py

# 4. Test endpoints using curl or Postman
curl http://localhost:8080/invoices/vendor/ACME
```

## Key Changes from Previous Version

1. ✅ Removed `db_util.py` with raw SQL queries
2. ✅ Removed `controllers/` package
3. ✅ Added SQLAlchemy ORM models
4. ✅ Added database-agnostic connection management
5. ✅ Converted tests from pytest to unittest
6. ✅ All CRUD operations use ORM instead of raw SQL
7. ✅ Support for both SQLite and PostgreSQL

## Running the Application

```bash
# Initialize database and start server
python3 app.py

# The application will:
# - Create database tables automatically
# - Start FastAPI server on http://localhost:8080
# - Use SQLite by default (or PostgreSQL if DB_BACKEND=postgres)
```

## API Endpoints

- **POST /extract**: Extract invoice from PDF file
- **GET /invoice/{invoice_id}**: Get invoice by ID
- **GET /invoices/vendor/{vendor_name}**: Get all invoices for a vendor

## Dependencies

- **fastapi**: Web framework
- **sqlalchemy**: ORM for database operations
- **psycopg2-binary**: PostgreSQL adapter
- **uvicorn**: ASGI server
- **oci**: Oracle Cloud Infrastructure SDK
- **httpx**: HTTP client for testing
