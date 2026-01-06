from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import oci
import base64
import time
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
    
    document = oci.ai_document.models.InlineDocumentDetails(
        data=encoded_pdf
    )
    
    request = oci.ai_document.models.AnalyzeDocumentDetails(
        document=document,
        features=[
            oci.ai_document.models.DocumentFeature(
                feature_type="KEY_VALUE_EXTRACTION"
            ),
            oci.ai_document.models.DocumentClassificationFeature(
                max_results=5
            )
        ]
    )
    
    try:
        start_time = time.time()
        response = doc_client.analyze_document(request)
        prediction_time = time.time() - start_time
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"error": "The service is currently unavailable. Please try again later."}
        )
    
    # ============ ADD YOUR CODE HERE ============
    data = {}
    data_confidence = {}
    items = []

    # Get the invoice confidence
    invoice_confidence = 1.0
    if response.data.detected_document_types:
        for doc_type in response.data.detected_document_types:
            if doc_type.document_type == "INVOICE":
                invoice_confidence = doc_type.confidence
                break

    # Extract fields from pages
    for page in response.data.pages:
        if page.document_fields:
            for field in page.document_fields:
                field_name = field.field_label.name if field.field_label else None
                field_confidence = field.field_label.confidence if field.field_label else None
                
                # Handle Items array specially
                if field_name == "Items":
                    if field.field_value.items:
                        for item in field.field_value.items:
                            item_data = {}
                            for item_field in item.field_value.items:
                                item_field_name = item_field.field_label.name
                                item_field_value = item_field.field_value.value
                                item_data[item_field_name] = item_field_value
                            items.append(item_data)
                else:
                    # Regular fields - use .value for typed data
                    field_value = field.field_value.value
                    data[field_name] = field_value
                    data_confidence[field_name] = field_confidence

    # Add items to data
    data["Items"] = items

    # Create result
    result = {
    "confidence": invoice_confidence,
    "data": data,
    "dataConfidence": data_confidence,
    "predictionTime": prediction_time
}

    # ============ END OF YOUR CODE ============
    
    # Check confidence
    if invoice_confidence < 0.9:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid document. Please upload a valid PDF invoice with high confidence."}
        )
    
    # Save to database
    print(f"DEBUG app.py: About to save invoice with ID: {result['data'].get('InvoiceId')}")
    try:
        save_inv_extraction(result)
        print("DEBUG app.py: save_inv_extraction returned successfully!")
    except Exception as e:
        print(f"DEBUG app.py ERROR: Failed to save - {e}")
        import traceback
        traceback.print_exc()
    
    return result


@app.get("/invoice/{invoice_id}")
async def get_invoice(invoice_id: str):
    invoice = get_invoice_by_id(invoice_id)
    if not invoice:
        return JSONResponse(
            status_code=404,
            content={"error": "Invoice not found"}
        )
    return invoice


@app.get("/invoices/vendor/{vendor_name}")
async def get_invoices_by_vendor_endpoint(vendor_name: str):
    invoices = get_invoices_by_vendor(vendor_name)
    return {
        "VendorName": vendor_name,
        "TotalInvoices": len(invoices),
        "invoices": invoices
    }


if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8080)



    #test Git
