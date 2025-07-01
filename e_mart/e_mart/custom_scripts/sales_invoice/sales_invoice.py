import frappe

def validate_buyback_fields(doc, method=None):
    """Calculate row amount, total buyback amount, and adjust outstanding amount if is_buyback is checked."""

    total = 0

    # 1. Calculate amount per row
    if doc.buyback_items:
        for row in doc.buyback_items:
            row.amount = (row.qty or 0) * (row.rate or 0)
            total += row.amount

    # 2. Set total buyback amount
    doc.buyback_amount = total

    # 3. Subtract buyback from outstanding amount
    if doc.is_buyback and doc.buyback_amount:
        doc.outstanding_amount = max((doc.outstanding_amount or 0) - doc.buyback_amount, 0)
