import frappe
from frappe.utils import flt,add_months,nowdate,get_first_day,get_last_day,add_days
from frappe.model.mapper import get_mapped_doc
from datetime import datetime
from frappe.utils import flt
from frappe.utils import get_url_to_form


def on_submit(doc, method=None):
	create_scrap_stock_entry(doc, method)
	create_buyback_journal_entry(doc, method)
	create_demo_tasks_on_submit(doc, method)
	update_monthly_commission_log(doc, method)

def validate_buyback_fields(doc, method=None):
	"""
	Triggered on validation of Sales Invoice.

	1. Calculates amount for each Buyback Item row.
	2. Sums up all row amounts into buyback_amount.
	3. Adjusts the outstanding_amount, rounded total and grand total if is_buyback check box is checked
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

	# 4. Set rounded_total and Grand Total
	grand_total = (doc.total or 0) + (doc.total_taxes_and_charges or 0)
	if doc.is_buyback and doc.buyback_amount:
		grand_total -= doc.buyback_amount
	doc.grand_total = grand_total
	doc.outstanding_amount = round(grand_total)
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
	down_payment = flt(doc.down_payment_amount)
	outstanding = flt(doc.outstanding_amount)
	doc.emi_amount = outstanding - down_payment

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
	finance_invoice.customer = sales_invoice.emi_provider
	finance_invoice.posting_date = frappe.utils.nowdate()
	finance_invoice.total_amount = sales_invoice.total
	finance_invoice.actual_customer = sales_invoice.customer
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
	
def create_buyback_journal_entry(doc, method):
	'''
	Create Buyback Journal entry for Buyback amount from Sales invoice.
	'''
	if not doc.is_buyback or not doc.buyback_amount or doc.buyback_amount <= 0:
		return

	customer_account = doc.debit_to
	if not customer_account:
		frappe.throw(f"Customer receivable account (debit_to) not found in Sales Invoice {doc.name}")

	company = doc.company or frappe.db.get_value("Sales Invoice", doc.name, "company")
	if not company:
		frappe.throw(f"Company not found for Sales Invoice {doc.name}")

	buyback_account = frappe.db.get_single_value("E-mart Settings", "buyback_posting_account")
	if not buyback_account:
		frappe.throw("Please set 'Buyback Posting Account' in E-mart Settings.")

	# Create Journal Entry
	journal_entry = frappe.new_doc("Journal Entry")
	journal_entry.voucher_type = "Credit Note"
	journal_entry.posting_date = nowdate()
	journal_entry.company = company
	journal_entry.remark = f"Buyback adjustment for Sales Invoice {doc.name}"

	# Credit Customer (receivable)
	journal_entry.append("accounts", {
		"account": customer_account,
		"party_type": "Customer",
		"party": doc.customer,
		"credit_in_account_currency": doc.buyback_amount,
		"reference_type": "Sales Invoice",
		"reference_name": doc.name
	})

	# Dedit Buyback Posting Account
	journal_entry.append("accounts", {
		"account": buyback_account,
		"debit_in_account_currency": doc.buyback_amount
	})

	journal_entry.insert(ignore_permissions=True)
	journal_entry.submit()

	# Optional: Save Journal Entry reference if field exists
	if frappe.get_meta(doc.doctype).has_field("buyback_journal_entry"):
		doc.db_set("buyback_journal_entry", journal_entry.name)

	frappe.msgprint(
		f'Buyback Journal Entry Created: <a href="{frappe.utils.get_url_to_form("Journal Entry", journal_entry.name)}" target="_blank"><b>{journal_entry.name}</b></a>',alert=True,indicator='green')

def create_demo_tasks_on_submit(doc, method=None):
	"""
	Create a Task for each Sales Invoice Item where is_demo_reqd is checked.
	Subject, Task Type, Minimal Duration, Escalation Duration come from E-mart Settings.
	Maps invoice_date, invoice_reference, customer, exp_start_date, and end_date into Task.
	"""

	settings = frappe.get_single("E-mart Settings")
	task_subject_template = settings.subject or "Demo Required - {item_name} [{invoice_name}]"
	task_type = settings.task_type or "Demo"
	minimal_duration = settings.minimal_duration or 0
	escalation_duration = settings.escalation_duration or 0

	for item in doc.items:
		if item.get("is_demo_reqd"):
			subject = task_subject_template.format(
				item_name=item.item_name,
				invoice_name=doc.name
			)

			exp_start_date = add_days(doc.posting_date, minimal_duration)
			end_date = add_days(doc.posting_date, escalation_duration)

			task = frappe.new_doc("Task")
			task.subject = subject
			task.type = task_type
			task.status = "Open"
			task.reference_type = "Sales Invoice"
			task.reference_name = doc.name
			task.description = (
				f"Demo required for Item: {item.item_name} ({item.item_code})\n"
				f"Qty: {item.qty}\n"
				f"Customer: {doc.customer}\n"
			)
			
			task.invoice_date = doc.posting_date
			task.invoice_reference = doc.name
			task.customer = doc.customer
			task.exp_start_date = exp_start_date
			task.exp_end_date = end_date

			task.insert(ignore_permissions=True)

def update_monthly_commission_log(doc, method):
	"""
	Create or update Monthly Commission Log for each Sales Person in the Sales Invoice.
	Logs incentives and invoice details for the respective employee and month.
	"""
	invoice_date = datetime.strptime(doc.posting_date, "%Y-%m-%d").date()
	month_start = get_first_day(invoice_date)
	month_end = get_last_day(invoice_date)
	month_name = invoice_date.strftime('%B')

	for sales_team_member in doc.sales_team:
		sales_person = sales_team_member.sales_person
		incentives = sales_team_member.incentive or 0

		# Get the Employee linked to Sales Person
		employee = frappe.db.get_value("Sales Person", sales_person, "employee")
		if not employee:
			frappe.log_error(
				f"Sales Person {sales_person} has no linked Employee.",
				"Monthly Commission Log"
			)
			continue

		# Check if Monthly Commission Log exists
		log_name = frappe.db.exists(
			"Monthly Commission Log",
			{
				"employee": employee,
				"log_month": month_name,
				"start_date": month_start,
				"end_date": month_end
			}
		)

		if log_name:
			log = frappe.get_doc("Monthly Commission Log", log_name)
		else:
			log = frappe.new_doc("Monthly Commission Log")
			log.employee = employee
			log.log_month = month_name
			log.start_date = month_start
			log.end_date = month_end

		# Append detail row
		log.append("monthly_commission_log", {
			"sales_invoice": doc.name,
			"date": invoice_date,
			"total_amount": doc.base_grand_total,
			"incentives": incentives
		})

		log.save(ignore_permissions=True)
		link = get_url_to_form("Monthly Commission Log", log.name)
		frappe.msgprint(
			f'Monthly Commission Log Created/Updated: <a href="{link}" target="_blank"><b>{log.name}</b></a>',
			alert=True,
			indicator='green'
		)

def calculate_total_expense(doc, method):
	"""
	Calculate and set the total of all sales_expenses in the document.
	"""
	total = 0

	for row in doc.get("sales_expenses", []):
		total += flt(row.amount or 0)
	doc.total_expense = total

# calculate incentives based on commission rate and allocated percentage
def map_commission_to_sales_team(doc, method):
	"""Fetch total_commission_rate to each sales_team row as allocated_amount and compute incentives."""
	commission_rate = doc.total_commission_rate or 0

	for row in doc.sales_team:
		row.total_commission_rate = commission_rate
		allocated_percentage = row.allocated_percentage or 0
		row.incentive = round((commission_rate * allocated_percentage) / 100, 2)

def calculate_profit_for_commission(doc, method):
	"""Calculates profit for commission for each item by subtracting its Sales Expense Contribution from the total expense."""
	total_expense = flt(doc.total_expense or 0)

	for item in doc.items:
		contribution = flt(item.sales_expense_contribution or 0)
		profit = total_expense - contribution
		item.profit_for_commission = profit

