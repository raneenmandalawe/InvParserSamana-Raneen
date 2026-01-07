# API Test Plan - InvParser Application

## 1. What to Test

### API Endpoints

Your application has **3 endpoints**:

1. **POST /extract** - Upload PDF and extract invoice data using OCI
2. **GET /invoice/{invoice_id}** - Retrieve invoice by ID
3. **GET /invoices/vendor/{vendor_name}** - Retrieve all invoices for a vendor

### Functionalities to Test

**Invoice Extraction (POST /extract)**
- Successful extraction with high confidence (≥0.9)
- Rejection of low confidence invoices (<0.9)
- OCI service unavailability handling
- Missing file validation

**Invoice Retrieval by ID (GET /invoice/{invoice_id})**
- Successful retrieval with valid ID
- 404 error for non-existent invoice

**Invoices by Vendor (GET /invoices/vendor/{vendor_name})**
- Successful retrieval with results
- Empty results for vendors with no invoices
- Special character handling (spaces in vendor names)
- Response structure validation

**Integration Workflows**
- Complete workflow: extract → retrieve
- Data persistence verification

## 2. Test Design Strategy

### Integration Testing with Mocking

**Approach:**
- Use FastAPI TestClient to simulate HTTP requests
- Use real SQLite database for data persistence
- Mock OCI Document AI service to avoid external dependencies

**Tools:**
- **pytest** - Test framework
- **FastAPI TestClient** - HTTP request simulation
- **unittest.mock** - Mock OCI service
- **Real SQLite Database** - Data persistence testing

**Test Structure:**
```
test/
├── __init__.py
└── test_api_integration.py    # All 12 test cases
```

## 3. Test Environment

- **Local Development**: Run tests on your machine
- **CI/CD**: GitHub Actions on every push/PR
- **Python Version**: 3.10+
- **Database**: SQLite (test instance)

## 4. Success Criteria

### Primary Goals
- ✅ **100% Endpoint Coverage** - All 3 endpoints tested
- ✅ **12 Test Cases** - Success, failure, and edge cases
- ✅ **Code Coverage**: Target ≥85%
- ✅ **All Tests Pass** - Zero failures

### Test Case Distribution

| Endpoint | Test Cases |
|----------|------------|
| POST /extract | 4 |
| GET /invoice/{id} | 2 |
| GET /invoices/vendor/{name} | 3 |
| Integration | 1 |
| **Total** | **10** |

## 5. Reporting

### Local Testing
```bash
# Run tests
pytest test/ -v

# Generate coverage report
pytest test/ --cov=app --cov=db_util --cov-report=html
open htmlcov/index.html
```

### CI/CD Reporting
- GitHub Actions workflow runs on every push
- Coverage uploaded to Codecov
- Test results visible in PR checks

### Documentation
- This test plan
- Traceability matrix (endpoint → test mapping)

## 6. Test Data Management

### Setup (setUp method)
- Initialize clean database
- Insert test data for retrieval tests
- Create TestClient instance

### Teardown (tearDown method)
- Drop all tables
- Clean database for next test
- Ensure test isolation

## 7. Mocking Strategy

### OCI Document AI Service
All tests mock the OCI service by patching `app.doc_client`:

```python
@patch('app.doc_client')
def test_extract_success(self, mock_doc_client):
    # Mock the analyze_document response
    mock_doc_client.analyze_document.return_value = mock_response
```

**Why mock?**
- No external API calls during testing
- No API costs
- Fast test execution
- Deterministic results

## 8. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| OCI service dependency | Complete mocking of OCI calls |
| Database state pollution | Clean database after each test |
| Flaky tests | Deterministic test data, no time dependencies |
| Schema changes | Tests use actual database schema |

## 9. Timeline

- **Setup**: 1 hour (add clean_db, install deps)
- **Run tests locally**: 10 minutes
- **CI/CD setup**: 30 minutes  
- **Total**: ~2 hours

## 10. Execution

### Run All Tests
```bash
pytest test/ -v
```

### Run Specific Test Class
```bash
pytest test/test_api_integration.py::TestExtractEndpoint -v
```

### Run With Coverage
```bash
pytest test/ --cov=app --cov=db_util --cov-report=html
```

## Notes

- **Confidence threshold**: 0.9 (90%)
- **Error codes**: 400 (low confidence), 404 (not found), 503 (service unavailable)
- **Database**: Uses real SQLite for authentic integration testing
- **Mocking**: Only external OCI service is mocked
