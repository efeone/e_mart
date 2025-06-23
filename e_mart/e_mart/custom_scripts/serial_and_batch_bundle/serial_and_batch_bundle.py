import frappe

def set_purchase_category_from_purchase_receipt(doc, method):
    '''
        Fetches and sets the purchase category from the Purchase Receipt to each entry row.
    '''
    if doc.voucher_type != "Purchase Receipt" or not doc.voucher_no:
        return
    try:
        purchase_receipt = frappe.get_doc("Purchase Receipt", doc.voucher_no)
    except frappe.DoesNotExistError:
        return

    purchase_category = purchase_receipt.get("purchase_category")
    if not purchase_category:
        return
    for row in doc.entries:
        row.purchase_category = purchase_category  # Set value in memory
    doc.save(ignore_permissions=True)
