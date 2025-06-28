import frappe

def update_schema_discount_amount(doc, method):
    """
    Updates the parent schema_discount_amount field with the sum of all child schema_discount_amount values.
    """
    total_schema_discount = 0

    for item in doc.items:
        if item.schema_discount_amount:
            total_schema_discount += item.schema_discount_amount

    doc.schema_discount_amount = total_schema_discount
