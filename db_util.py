import sqlite3
from contextlib import contextmanager

DB_PATH = "invoices.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                InvoiceId TEXT PRIMARY KEY,
                VendorName TEXT,
                InvoiceDate TEXT,
                BillingAddressRecipient TEXT,
                ShippingAddress TEXT,
                SubTotal REAL,
                ShippingCost REAL,
                InvoiceTotal REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS confidences (
                InvoiceId TEXT PRIMARY KEY,
                VendorName REAL,
                InvoiceDate REAL,
                BillingAddressRecipient REAL,
                ShippingAddress REAL,
                SubTotal REAL,
                ShippingCost REAL,
                InvoiceTotal REAL,
                FOREIGN KEY (InvoiceId) REFERENCES invoices(InvoiceId)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                InvoiceId TEXT,
                Description TEXT,
                Name TEXT,
                Quantity REAL,
                UnitPrice REAL,
                Amount REAL,
                FOREIGN KEY (InvoiceId) REFERENCES invoices(InvoiceId)
            )
        """)

def save_inv_extraction(result):
    try:
        data = result.get("data", {})
        data_confidence = result.get("dataConfidence", {})
        invoice_id = data.get("InvoiceId")
        
        print(f"DEBUG db_util: invoice_id = {invoice_id}")
        print(f"DEBUG db_util: invoice_id type = {type(invoice_id)}")
        
        if invoice_id:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Insert invoice
                cursor.execute("""
                    INSERT OR REPLACE INTO invoices 
                    (InvoiceId, VendorName, InvoiceDate, BillingAddressRecipient, 
                     ShippingAddress, SubTotal, ShippingCost, InvoiceTotal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    invoice_id,
                    data.get("VendorName"),
                    data.get("InvoiceDate"),
                    data.get("BillingAddressRecipient"),
                    data.get("ShippingAddress"),
                    data.get("SubTotal"),
                    data.get("ShippingCost"),
                    data.get("InvoiceTotal")
                ))
                
                print(f"DEBUG db_util: Invoice inserted")
                
                # Insert confidences
                cursor.execute("""
                    INSERT OR REPLACE INTO confidences 
                    (InvoiceId, VendorName, InvoiceDate, BillingAddressRecipient,
                     ShippingAddress, SubTotal, ShippingCost, InvoiceTotal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    invoice_id,
                    data_confidence.get("VendorName"),
                    data_confidence.get("InvoiceDate"),
                    data_confidence.get("BillingAddressRecipient"),
                    data_confidence.get("ShippingAddress"),
                    data_confidence.get("SubTotal"),
                    data_confidence.get("ShippingCost"),
                    data_confidence.get("InvoiceTotal")
                ))
                
                print(f"DEBUG db_util: Confidences inserted")
                
                # Delete old items for this invoice (to avoid duplicates)
                cursor.execute("DELETE FROM items WHERE InvoiceId = ?", (invoice_id,))
                
                # Insert line items
                line_items = data.get("Items", [])
                print(f"DEBUG db_util: Number of items to insert: {len(line_items)}")
                
                for item in line_items:
                    cursor.execute("""
                        INSERT INTO items 
                        (InvoiceId, Description, Name, Quantity, UnitPrice, Amount)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        invoice_id,
                        item.get("Description"),
                        item.get("Name"),
                        item.get("Quantity"),
                        item.get("UnitPrice"),
                        item.get("Amount")
                    ))
                
                print(f"DEBUG db_util: Items inserted")
            
            print(f"DEBUG db_util: Successfully saved invoice {invoice_id}")
        else:
            print(f"DEBUG db_util: No invoice_id found in data!")  # pragma: no cover
            
    except Exception as e:  # pragma: no cover
        print(f"DEBUG db_util ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise

def clean_db():
    """Clean the database by dropping all tables."""
    with get_db() as conn:
        cursor = conn.cursor()
        # Drop tables in reverse order of dependencies
        cursor.execute("DROP TABLE IF EXISTS items")
        cursor.execute("DROP TABLE IF EXISTS confidences")
        cursor.execute("DROP TABLE IF EXISTS invoices")

def get_invoice_by_id(invoice_id):
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get invoice data
        cursor.execute("SELECT * FROM invoices WHERE InvoiceId = ?", (invoice_id,))
        invoice_row = cursor.fetchone()
        
        if not invoice_row:
            return None
        
        # Convert to dictionary
        invoice = dict(invoice_row)
        
        # Get items
        cursor.execute("SELECT Description, Name, Quantity, UnitPrice, Amount FROM items WHERE InvoiceId = ?", (invoice_id,))
        items_rows = cursor.fetchall()
        
        # Add items to invoice
        invoice["Items"] = [dict(item) for item in items_rows]
        
        return invoice


def get_invoices_by_vendor(vendor_name):
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all invoices from this vendor
        cursor.execute("SELECT * FROM invoices WHERE VendorName = ?", (vendor_name,))
        invoice_rows = cursor.fetchall()
        
        invoices = []
        for invoice_row in invoice_rows:
            invoice = dict(invoice_row)
            
            # Get items for this invoice
            cursor.execute("SELECT Description, Name, Quantity, UnitPrice, Amount FROM items WHERE InvoiceId = ?", (invoice["InvoiceId"],))
            items_rows = cursor.fetchall()
            invoice["Items"] = [dict(item) for item in items_rows]
            
            invoices.append(invoice)
        
        return invoices
