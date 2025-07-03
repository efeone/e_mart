import frappe

def set_purchase_category_from_voucher(doc, method):
    '''
    Fetches and sets the purchase category from either Purchase Receipt or Purchase Invoice
    to each entry row.
    '''
    if doc.voucher_type not in ["Purchase Receipt", "Purchase Invoice", "Stock Reconciliation"] or not doc.voucher_no:
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

def set_purchase_category_on_creation(doc, method=None):
    """
    On creation of Serial and Batch Bundle, set Purchase Category
    in child entries if Serial No or Batch No was already used elsewhere.
    """
    updated = False

    for entry in doc.entries:
        if entry.purchase_category:
            continue 

        purchase_category = None

        if entry.serial_no:
            purchase_category = frappe.db.get_value(
                "Serial and Batch Entry",
                {
                    "serial_no": entry.serial_no,
                    "parent": ["!=", doc.name]
                },
                "purchase_category",
                order_by="creation desc"
            )

        if not purchase_category and entry.batch_no:
            purchase_category = frappe.db.get_value(
                "Serial and Batch Entry",
                {
                    "batch_no": entry.batch_no,
                    "parent": ["!=", doc.name]
                },
                "purchase_category",
                order_by="creation desc"
            )

        if purchase_category:
            entry.purchase_category = purchase_category
            updated = True

    if updated:
        doc.save(ignore_permissions=True)