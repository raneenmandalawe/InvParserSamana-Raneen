from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import base64
import oci

from db_util import init_db, save_inv_extraction, get_invoice_by_id, get_invoices_by_vendor

app = FastAPI()

# Load OCI config from ~/.oci/config
config = oci.config.from_file()
doc_client = oci.ai_document.AIServiceDocumentClient(config)


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    pdf_bytes = await file.read()

    # Base64 encode PDF
    encoded_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

    document = oci.ai_document.models.InlineDocumentDetails(data=encoded_pdf)

    request = oci.ai_document.models.AnalyzeDocumentDetails(
        document=document,
        features=[
            oci.ai_document.models.DocumentFeature(feature_type="KEY_VALUE_EXTRACTION"),
            oci.ai_document.models.DocumentClassificationFeature(max_results=5),
        ],
    )

    try:
        response = doc_client.analyze_document(request)
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"error": "The service is currently unavailable. Please try again later."},
        )

    data = {}
    data_confidence = {}
    items = []

    # Get the invoice confidence
    invoice_confidence = 1.0
    detected_types = getattr(response.data, "detected_document_types", None) or []
    for doc_type in detected_types:
        if getattr(doc_type, "document_type", None) == "INVOICE":
            invoice_confidence = getattr(doc_type, "confidence", 1.0)
            break

    # Extract fields from pages
    pages = getattr(response.data, "pages", None) or []
    for page in pages:
        for field in getattr(page, "document_fields", None) or []:
            field_label = getattr(field, "field_label", None)
            field_name = getattr(field_label, "name", None)
            field_conf = getattr(field_label, "confidence", None)

            # Handle Items array specially
            if field_name == "Items":
                field_value = getattr(field, "field_value", None)
                for item in getattr(field_value, "items", None) or []:
                    item_data = {}
                    for item_field in getattr(item.field_value, "items", None) or []:
                        item_field_label = getattr(item_field, "field_label", None)
                        item_field_name = getattr(item_field_label, "name", None)
                        item_field_value = getattr(item_field.field_value, "value", None)
                        if item_field_name is not None:
                            item_data[item_field_name] = item_field_value
                    items.append(item_data)
            else:
                # Regular fields
                field_value_obj = getattr(field, "field_value", None)
                field_value = getattr(field_value_obj, "value", None)
                if field_name is not None:
                    data[field_name] = field_value
                    data_confidence[field_name] = field_conf

    data["Items"] = items

    result = {
        "confidence": invoice_confidence,
        "data": data,
        "dataConfidence": data_confidence,
    }

    # Check confidence
    if invoice_confidence < 0.9:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid document. Please upload a valid PDF invoice with high confidence."},
        )

    # Save to database (do not fail the endpoint if DB save fails)
    try:
        save_inv_extraction(result)
    except Exception:
        pass

    return result


@app.get("/invoice/{invoice_id}")
async def get_invoice(invoice_id: str):
    invoice = get_invoice_by_id(invoice_id)
    if not invoice:
        return JSONResponse(status_code=404, content={"error": "Invoice not found"})
    return invoice


@app.get("/invoices/vendor/{vendor_name}")
async def get_invoices_by_vendor_endpoint(vendor_name: str):
    invoices = get_invoices_by_vendor(vendor_name)
    return {"VendorName": vendor_name, "TotalInvoices": len(invoices), "invoices": invoices}


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8080)
