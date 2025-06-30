# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

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

def on_submit(doc, method):
    create_debit_note_log(doc)

def create_debit_note_log(purchase_invoice):
    '''
        Creates a Debit Note Log from a submitted Purchase Invoice
    '''
    exists = frappe.db.exists("Debit Note Log", {"purchase_invoice": purchase_invoice.name})
    if exists:
        frappe.msgprint(f"Debit Note Log already exists for {purchase_invoice.name}")
        return

    # Create new Debit Note Log
    dnl = frappe.new_doc("Debit Note Log")
    dnl.supplier = purchase_invoice.supplier
    dnl.purchase_invoice = purchase_invoice.name
    dnl.purchase_schema = purchase_invoice.purchase_schema
    dnl.status = "Pending"
    dnl.total_invoice_amount = purchase_invoice.total
    dnl.discounted_amount = purchase_invoice.schema_discount_amount

    # Add items from Purchase Invoice
    for item in purchase_invoice.items:
        dnl.append("items", {
            "item": item.item_code,
            "item_name": item.item_name,
            "quantity": item.qty,
            "rate": item.rate,
            "discount": item.schema_discount_amount
        })

    dnl.insert(ignore_permissions=True)
    frappe.msgprint(f"Debit Note Log <a href='/app/debit-note-log/{dnl.name}'>{dnl.name}</a> created.")
