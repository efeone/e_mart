# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

import base64
from io import BytesIO
from barcode import Code128
from barcode.writer import ImageWriter
import frappe

from frappe.model.document import Document


class BarcodeTool(Document):
	pass

@frappe.whitelist()
def generate_barcode(in_val):
    stream = BytesIO()
    Code128(str(in_val), writer=ImageWriter()).write(
        stream,
        {
            "module_height": 3,
            "text_distance": 0.9,
            "write_text": False,
        }
    )
    barcode_base64 = base64.b64encode(stream.getvalue()).decode()
    stream.close()
    return barcode_base64

@frappe.whitelist()
def fetch_items_from_purchase(purchase_doc):
    pr = frappe.get_doc("Purchase Receipt", purchase_doc)
    items = []
    for d in pr.items:
        items.append({
            "item_code": d.item_code,
            "item_name": d.item_name,
            "qty": d.qty
        })
    return items

@frappe.whitelist()
def render_item_barcode(item_code):
    """
    Render only the body of 'Item BarcodeTool' format (no letterhead/page wrapper).
    """
    print("called for ", item_code)
    if not item_code:
        return ""

    item = frappe.get_doc("Item", item_code)
    mrp = item.get("mrp")
    erp = item.get("valuation_rate")

    # Load the print format template
    template = frappe.get_doc("Print Format", "Item Barcode").html

    # Render using frappe.render_template
    html = frappe.render_template(template, {
        "doc": item,
        "mrp": mrp,
        "erp": erp
    })

    return html

@frappe.whitelist()
def fetch_items_from_documents(doctype, docnames):
    import json
    docnames = json.loads(docnames) if isinstance(docnames, str) else docnames
    items = []

    for name in docnames:
        doc = frappe.get_doc(doctype, name)
        for d in doc.items:
            items.append({
                "item_code": d.item_code,
                "item_name": d.item_name,
                "qty": d.qty
            })

    return items

