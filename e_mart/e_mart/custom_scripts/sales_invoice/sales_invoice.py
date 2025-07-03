import frappe
from frappe.utils import flt,add_months

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

def update_emi_amount(doc, method):
	"""
	Generate the emi amount after deducting the down payment
	"""
	down_payment = doc.down_payment_amount or 0
	total = doc.total or 0
	doc.emi_amount = total - down_payment

# def generate_emi_schedule(doc, method):
# 	"""
# 	Generate EMI Duration table rows based on customer emi_start_date and number of installments
# 	"""
# 	if doc.sales_type != "EMI":
# 		return

# 	if not doc.customer:
# 		frappe.throw("Please select a Customer.")

# 	customer = frappe.get_doc("Customer", doc.customer)
# 	emi_start_date = customer.get("emi_start_date")
# 	if not emi_start_date:
# 		frappe.throw("Customer does not have an EMI Start Date.")

# 	no_of_installments = doc.get("no_of_installment")
# 	if not no_of_installments:
# 		frappe.throw("Please set No of Installments")

# 	emi_amount = doc.get("emi_amount")  
# 	doc.set("emi_duration", [])

# 	installment_amount = flt(emi_amount) / int(no_of_installments)

# 	for i in range(int(no_of_installments)):
# 		installment_date = add_months(emi_start_date, i)
# 		doc.append("emi_duration", {
# 			"date": installment_date,
# 			"amount": installment_amount
# 		})

def generate_emi_schedule(doc, method):
	"""
	Generate EMI Duration table rows based on:
	- doc.emi_date (Sales Invoice EMI start date)
	- no_of_installments
	- emi_amount
	"""
	if doc.sales_type != "EMI":
		return

	if not doc.emi_date:
		frappe.throw("Please set the EMI Start Date in Sales Invoice.")

	if not doc.no_of_installment:
		frappe.throw("Please set No of Installments.")

	if not doc.emi_amount:
		frappe.throw("Please set EMI Amount.")

	doc.set("emi_duration", [])  # Clear existing table

	installment_amount = flt(doc.emi_amount) / int(doc.no_of_installment)

	for i in range(int(doc.no_of_installment)):
		installment_date = add_months(doc.emi_date, i)
		doc.append("emi_duration", {
			"date": installment_date,
			"amount": installment_amount
		})		

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

