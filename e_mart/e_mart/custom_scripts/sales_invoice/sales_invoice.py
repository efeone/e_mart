import frappe
from frappe.utils import flt

def validate_buyback_fields(doc, method=None):

	"""
	Triggered on validation of Sales Invoice.

	1. Calculates amount for each Buyback Item row.
	2. Sums up all row amounts into buyback_amount.
	3. Adjusts the outstanding_amount if is_buyback is checked.
	"""

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

def create_scrap_stock_entry(doc, method):
	"""
	On submission of Sales Invoice:
	Creates a Stock Entry to move Buyback Items to Scrap Warehouse
	(Scrap warehouse is fetched from E-mart Settings).
	"""

	if not doc.buyback_items:
		return

	scrap_warehouse = frappe.db.get_single_value("E-mart Settings", "scrap_warehouse")
	if not scrap_warehouse:
		frappe.throw("Please set the Scrap Warehouse in E-mart Settings.")

	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.purpose = "Material Receipt"
	stock_entry.stock_entry_type = "Material Receipt"
	stock_entry.company = doc.company
	stock_entry.to_warehouse = scrap_warehouse
	stock_entry.sales_invoice_no = doc.name  # Optional

	for row in doc.buyback_items:
		if row.item and flt(row.qty) > 0:
			stock_entry.append("items", {
				"item_code": row.item,
				"qty": row.qty,
				"uom": "Nos",  # adjust as needed
				"t_warehouse": scrap_warehouse,
				"basic_rate": row.rate
			})

	stock_entry.insert()
	stock_entry.submit()
	frappe.msgprint(f' Scrap Stock Entry Created: <a href="{frappe.utils.get_url_to_form(stock_entry.doctype, stock_entry.name)}" target="_blank"><b>{stock_entry.name}</b></a>',alert=True,indicator='green')

@frappe.whitelist()
def create_finance_invoice(sales_invoice_name):
    '''
    Create Finance Invoice from Sales Invoice
    '''
    sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)

    finance_invoice = frappe.new_doc("Finance Invoice")
    finance_invoice.customer = sales_invoice.customer
    finance_invoice.posting_date = frappe.utils.nowdate()
    finance_invoice.total_amount = sales_invoice.total
    finance_invoice.actual_customer = sales_invoice.actual_customer
    finance_invoice.total_taxes_and_charges = sales_invoice.total_taxes_and_charges

    for item in sales_invoice.items:
        finance_invoice.append("items", {
            "actual_item": item.item_code,
            "qty": item.qty,
            "rate": item.rate,
            "amount": item.amount
        })

    for tax in sales_invoice.taxes:
        finance_invoice.append("sales_taxes_and_charges", {
            "charge_type": tax.charge_type,
            "account_head": tax.account_head,
            "description": tax.description,
            "rate": tax.rate,
            "tax_amount": tax.tax_amount,
            "total": tax.total,
            "tax_amount_after_discount_amount": tax.tax_amount_after_discount_amount
        })

    finance_invoice.save(ignore_permissions=True)

    return finance_invoice.name
