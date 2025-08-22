import frappe
import re

def before_insert(doc, method):
    """
    Auto-generate a unique barcode using the given prefix (barcode_series).
    Example: If barcode_series = 'AAA', barcodes will be AAA1, AAA2, etc.
    """
    if not doc.barcodes:
        settings = frappe.get_single("E-mart Settings")
        prefix = settings.barcode_series or ""   # this is now the prefix itself

        if not prefix:
            frappe.throw("Please set a Barcode Series (prefix) in E-mart Settings")

        # Find last numeric suffix used for this prefix
        last = frappe.db.sql("""
            SELECT barcode
            FROM `tabItem Barcode`
            WHERE barcode LIKE %s
            ORDER BY LENGTH(barcode) DESC, barcode DESC
            LIMIT 1
        """, (prefix + "%",))

        if last and last[0][0]:
            # Extract numeric suffix from last barcode
            match = re.search(rf'^{re.escape(prefix)}(\d+)$', last[0][0])
            last_num = int(match.group(1)) if match else 0
        else:
            last_num = 0

        next_num = last_num + 1
        next_code = f"{prefix}{next_num}"

        # Append to Item Barcode child table
        doc.append("barcodes", {
            "barcode": next_code,
            "barcode_type": "Code128"
        })
