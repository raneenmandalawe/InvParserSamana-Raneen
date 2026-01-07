# API Traceability Matrix

| Endpoint | Method | Behavior / Scenario | Test Case |
|---|---:|---|---|
| /extract | POST | success (confidence >= 0.9) saves invoice + items | `test_extract_success_saves_and_returns` |
| /extract | POST | low confidence returns 400, no save | `test_extract_low_confidence_returns_400_no_save` |
| /extract | POST | OCI exception returns 503 | `test_extract_oci_exception_returns_503` |
| /invoice/{invoice_id} | GET | invoice exists returns invoice + items | `test_get_invoice_found` |
| /invoice/{invoice_id} | GET | invoice missing returns 404 | `test_get_invoice_not_found_404` |
| /invoices/vendor/{vendor_name} | GET | vendor summary + list | `test_get_invoices_by_vendor_summary` |
