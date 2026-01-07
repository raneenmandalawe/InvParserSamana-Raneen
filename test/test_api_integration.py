# test/test_api_integration.py
from types import SimpleNamespace
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from db_util import init_db, clean_db, get_invoice_by_id


def _make_field(name, value, confidence=0.99):
    return SimpleNamespace(
        field_label=SimpleNamespace(name=name, confidence=confidence),
        field_value=SimpleNamespace(value=value, items=None),
    )


def _make_item_field(name, value):
    return SimpleNamespace(
        field_label=SimpleNamespace(name=name, confidence=0.99),
        field_value=SimpleNamespace(value=value),
    )


def _make_items_field(items_list):
    """
    Build the special "Items" field in the structure your extraction code expects:
    field.field_value.items -> list of item
    item.field_value.items -> list of item_field
    """
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


def setup_function():
    # Run before each test
    init_db()


def teardown_function():
    # Run after each test
    clean_db()
    # Recreate tables so next test starts clean with schema present
    init_db()


def test_extract_success_saves_and_returns(app_module):
    # Arrange
    mock_client = app_module.doc_client
    mock_client.analyze_document.return_value = build_oci_response(
        invoice_confidence=0.95,
        fields={
            "InvoiceId": "INV-001",
            "VendorName": "ACME",
            "InvoiceDate": "2026-01-01",
            "BillingAddressRecipient": "John Doe",
            "ShippingAddress": "Tel Aviv",
            "SubTotal": 100.0,
            "ShippingCost": 10.0,
            "InvoiceTotal": 110.0,
        },
        items=[
            {
                "Description": "Product A",
                "Name": "A",
                "Quantity": 2,
                "UnitPrice": 50.0,
                "Amount": 100.0,
            }
        ],
    )

    client = TestClient(app_module.app)

    # Act
    resp = client.post(
        "/extract",
        files={"file": ("invoice.pdf", b"%PDF-1.4 fake pdf bytes", "application/pdf")},
    )

    # Assert: API response
    assert resp.status_code == 200
    body = resp.json()
    assert body["confidence"] >= 0.9
    assert body["data"]["InvoiceId"] == "INV-001"
    assert body["data"]["VendorName"] == "ACME"
    assert isinstance(body["data"]["Items"], list)
    assert body["data"]["Items"][0]["Description"] == "Product A"

    # Assert: saved to DB
    saved = get_invoice_by_id("INV-001")
    assert saved is not None
    assert saved["VendorName"] == "ACME"
    assert len(saved["Items"]) == 1
    assert saved["Items"][0]["Name"] == "A"


def test_extract_low_confidence_returns_400_no_save(app_module):
    mock_client = app_module.doc_client
    mock_client.analyze_document.return_value = build_oci_response(
        invoice_confidence=0.50,
        fields={
            "InvoiceId": "INV-LOW",
            "VendorName": "LOWVENDOR",
        },
        items=[],
    )

    client = TestClient(app_module.app)
    resp = client.post(
        "/extract",
        files={"file": ("invoice.pdf", b"%PDF-1.4 fake pdf bytes", "application/pdf")},
    )

    assert resp.status_code == 400
    assert resp.json()["error"].lower().startswith("invalid document")

    # Should not save to DB
    assert get_invoice_by_id("INV-LOW") is None


def test_extract_oci_exception_returns_503(app_module):
    mock_client = app_module.doc_client
    mock_client.analyze_document.side_effect = Exception("OCI down")

    client = TestClient(app_module.app)
    resp = client.post(
        "/extract",
        files={"file": ("invoice.pdf", b"%PDF-1.4 fake pdf bytes", "application/pdf")},
    )

    assert resp.status_code == 503
    assert "unavailable" in resp.json()["error"].lower()


def test_get_invoice_found(app_module):
    # Insert data via /extract first (integration style)
    mock_client = app_module.doc_client
    mock_client.analyze_document.return_value = build_oci_response(
        invoice_confidence=0.95,
        fields={
            "InvoiceId": "INV-GET-1",
            "VendorName": "V1",
            "InvoiceDate": "2026-01-02",
            "InvoiceTotal": 42.0,
        },
        items=[{"Description": "X", "Name": "X", "Quantity": 1, "UnitPrice": 42, "Amount": 42}],
    )

    client = TestClient(app_module.app)
    r1 = client.post(
        "/extract",
        files={"file": ("invoice.pdf", b"pdf", "application/pdf")},
    )
    assert r1.status_code == 200

    r2 = client.get("/invoice/INV-GET-1")
    assert r2.status_code == 200
    inv = r2.json()
    assert inv["InvoiceId"] == "INV-GET-1"
    assert inv["VendorName"] == "V1"
    assert len(inv["Items"]) == 1


def test_get_invoice_not_found_404(app_module):
    client = TestClient(app_module.app)
    resp = client.get("/invoice/DOES-NOT-EXIST")
    assert resp.status_code == 404
    assert resp.json()["error"] == "Invoice not found"


def test_get_invoices_by_vendor_summary(app_module):
    # Create two invoices for same vendor via /extract
    client = TestClient(app_module.app)
    mock_client = app_module.doc_client

    mock_client.analyze_document.return_value = build_oci_response(
        invoice_confidence=0.95,
        fields={"InvoiceId": "INV-V-1", "VendorName": "ACME", "InvoiceTotal": 10.0},
        items=[],
    )
    assert client.post("/extract", files={"file": ("a.pdf", b"a", "application/pdf")}).status_code == 200

    mock_client.analyze_document.return_value = build_oci_response(
        invoice_confidence=0.95,
        fields={"InvoiceId": "INV-V-2", "VendorName": "ACME", "InvoiceTotal": 20.0},
        items=[],
    )
    assert client.post("/extract", files={"file": ("b.pdf", b"b", "application/pdf")}).status_code == 200

    resp = client.get("/invoices/vendor/ACME")
    assert resp.status_code == 200
    data = resp.json()

    assert data["VendorName"] == "ACME"
    assert data["TotalInvoices"] == 2
    assert len(data["invoices"]) == 2
    ids = {inv["InvoiceId"] for inv in data["invoices"]}
    assert ids == {"INV-V-1", "INV-V-2"}
def test_extract_db_save_failure_still_returns_200(app_module, monkeypatch):
    # Arrange: OCI returns a valid invoice (confidence >= 0.9)
    app_module.doc_client.analyze_document.return_value = build_oci_response(
        invoice_confidence=0.95,
        fields={"InvoiceId": "INV-SAVE-FAIL", "VendorName": "ACME"},
        items=[],
    )

    # Force DB save to fail to cover the "except Exception: pass" lines
    def boom(_result):
        raise Exception("DB write failed")

    monkeypatch.setattr(app_module, "save_inv_extraction", boom)

    client = TestClient(app_module.app)

    # Act
    resp = client.post(
        "/extract",
        files={"file": ("invoice.pdf", b"%PDF-1.4", "application/pdf")},
    )

    # Assert: endpoint should still return success result
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["InvoiceId"] == "INV-SAVE-FAIL"
    assert body["confidence"] >= 0.9
