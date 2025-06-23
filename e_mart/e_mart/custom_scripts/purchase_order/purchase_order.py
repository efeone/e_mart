import frappe

def fetch_purchase_category(doc, method=None):
    '''
        Sets the purchase category in the document based on the linked Purchase Order of items.
    '''
    for item in doc.items:
        if item.purchase_order:
            po_category = frappe.db.get_value("Purchase Order", item.purchase_order, "purchase_category")
            if po_category:
                doc.purchase_category = po_category
