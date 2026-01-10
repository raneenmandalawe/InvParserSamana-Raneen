# InvParser API – Test Plan (Integration)

## What to test
API endpoints:
1. **POST /extract**
   - Success: valid invoice (confidence >= 0.9) → returns extraction JSON and saves to DB
   - Failure: low confidence (< 0.9) → 400 and does not save
   - Failure: OCI service error/exception → 503

2. **GET /invoice/{invoice_id}**
   - Success: invoice exists → returns invoice + items
   - Failure: invoice does not exist → 404

3. **GET /invoices/vendor/{vendor_name}**
   - Returns vendor summary (VendorName, TotalInvoices, invoices list)
   - Validate TotalInvoices and invoice content

## Test design strategy
- **Integration tests**:
  - Use **FastAPI TestClient** (no Uvicorn).
  - Use **real SQLite** database (`invoices.db`) via `db_util.init_db()` / `db_util.clean_db()`.
  - **Mock OCI Document AI** (`oci.config.from_file`, `oci.ai_document.AIServiceDocumentClient`) to avoid external dependency.

Framework:
- **pytest** + `unittest.mock`

## Test environment
- Local runs: `pytest test/ -v`
- CI: GitHub Actions workflow (`.github/workflows/test.yml`)
- Coverage: `pytest-cov` produces `coverage.xml` + HTML report.

## Success criteria
- **100% API endpoint coverage**
- As close as possible to **100% code coverage of API code** (`app.py`)
- All tests green in CI

## Reporting
- Console results from pytest in CI
- Coverage report uploaded to Codecov (coverage % visible in PR checks)
- Local HTML report in `htmlcov/index.html`
