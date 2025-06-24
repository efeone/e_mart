import frappe

def set_purchase_category_from_voucher(doc, method):
    '''
    Fetches and sets the purchase category from either Purchase Receipt or Purchase Invoice
    to each entry row.
    '''
    if doc.voucher_type not in ["Purchase Receipt", "Purchase Invoice"] or not doc.voucher_no:
        return

    try:
        source_doc = frappe.get_doc(doc.voucher_type, doc.voucher_no)
    except frappe.DoesNotExistError:
        return

    purchase_category = source_doc.get("purchase_category")
    if not purchase_category:
        return

    for row in doc.entries:
        row.purchase_category = purchase_category

    doc.save(ignore_permissions=True)
