import frappe
from frappe.utils import flt,add_months
from frappe.model.mapper import get_mapped_doc


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

	# 3.Calculate outstanding amount
	grand_total = (doc.total or 0) + (doc.total_taxes_and_charges or 0)
	if doc.is_buyback and doc.buyback_amount:
		grand_total -= doc.buyback_amount
	doc.outstanding_amount = round(grand_total)

	# 4. Set rounded_total
	grand_total = (doc.total or 0) + (doc.total_taxes_and_charges or 0)
	if doc.is_buyback and doc.buyback_amount:
		grand_total -= doc.buyback_amount
	doc.rounded_total = round(grand_total)

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

def generate_emi_schedule(doc, method):
	"""
	Generate EMI Duration table rows based on:
	- doc.emi_date (Sales Invoice EMI start date)
	- no_of_installments
	- emi_amount
	"""
	if doc.sales_type != "EMI":
		return
	if doc.is_buyback: 
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

#
@frappe.whitelist()

def make_down_payment_entry(source_name, target_doc=None):
	def set_missing_values(source, target):
		"""
		Create a Payment Entry from a Sales Invoice for down payment.
		Replaces total payment with down payment amount and map hte details.
		
		"""
		down_payment = source.down_payment_amount
		target.payment_type = "Receive"
		target.party_type = "Customer"
		target.paid_amount = down_payment
		target.received_amount = down_payment

		paid_from = frappe.get_value("Company", source.company, "default_receivable_account")
		paid_to = frappe.get_value("Company", source.company, "default_bank_account")

		target.paid_from = paid_from
		target.paid_to = paid_to
		target.posting_date = frappe.utils.nowdate()

		paid_from_currency = frappe.get_value("Account", paid_from, "account_currency")
		paid_to_currency = frappe.get_value("Account", paid_to, "account_currency")

		target.paid_from_account_currency = paid_from_currency
		target.paid_to_account_currency = paid_to_currency

		target.append("references", {
			"reference_doctype": "Sales Invoice",
			"reference_name": source.name,
			"total_amount": source.rounded_total,
			"outstanding_amount": source.outstanding_amount,
			"allocated_amount": down_payment
		})

	doc = get_mapped_doc(
		"Sales Invoice",
		source_name,
		{
			"Sales Invoice": {
				"doctype": "Payment Entry",
				"field_map": {
					"customer": "party",
					"customer_name": "party_name",
					"company": "company"
				}
			}
		},
		target_doc,
		set_missing_values
	)
	return doc

# calculate incentives based on commission rate and allocated percentage
def map_commission_to_sales_team(doc, method):
	"""Fetch total_commission_rate to each sales_team row as allocated_amount and compute incentives."""
	commission_rate = doc.total_commission_rate or 0

	for row in doc.sales_team:
		row.allocated_amount = commission_rate
		allocated_percentage = row.allocated_percentage or 0
		row.incentives = round((commission_rate * allocated_percentage) / 100, 2)

