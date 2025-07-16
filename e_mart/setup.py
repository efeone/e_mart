import os
import click
import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
	create_custom_fields(get_purchase_order_custom_fields(), ignore_validate=True, update=True)
	create_custom_fields(get_purchase_receipt_custom_fields(), ignore_validate=True, update=True)
	create_custom_fields(get_purchase_invoice_custom_fields(), ignore_validate=True, update=True)
	create_custom_fields(get_sales_order_item_custom_fields(), ignore_validate=True, update=True)
	create_custom_fields(get_sales_invoice_item_custom_fields(), ignore_validate=True, update=True)
	create_custom_fields(get_serial_and_batch_entry_custom_fields(), ignore_validate=True, update=True)
	create_custom_fields(get_purchase_invoice_item_custom_fields(), ignore_validate=True, update=True)
	create_custom_fields(get_item_custom_fields(), ignore_validate=True, update=True)
	create_custom_fields(get_customer_custom_fields(), ignore_validate=True, update=True)
	create_custom_fields(get_stock_reconciliation_custom_fields(), ignore_validate=True, update=True)
	create_custom_fields(get_sales_invoice_custom_fields(), ignore_validate=True, update=True)
	create_custom_fields(get_task_custom_fields(), ignore_validate=True, update=True)
	create_custom_fields(get_mode_of_payment_custom_fields(), ignore_validate=True, update=True)
	create_custom_fields(get_sales_order_custom_fields(),ignore_validate=True,update=True)
	create_custom_fields(get_sales_team_custom_fields(),ignore_validate=True,update=True)

	create_property_setters(get_property_setters())

def after_migrate():
	after_install()

def before_uninstall():
	delete_custom_fields(get_purchase_order_custom_fields())
	delete_custom_fields(get_purchase_receipt_custom_fields())
	delete_custom_fields(get_purchase_invoice_custom_fields())
	delete_custom_fields(get_sales_order_item_custom_fields())
	delete_custom_fields(get_sales_invoice_item_custom_fields())
	delete_custom_fields(get_serial_and_batch_entry_custom_fields())
	delete_custom_fields(get_purchase_invoice_item_custom_fields())
	delete_custom_fields(get_item_custom_fields())
	delete_custom_fields(get_customer_custom_fields())
	delete_custom_fields(get_stock_reconciliation_custom_fields())
	delete_custom_fields(get_sales_invoice_custom_fields())
	delete_custom_fields(get_task_custom_fields())
	delete_custom_fields(get_mode_of_payment_custom_fields())
	delete_custom_fields(get_sales_order_custom_fields())
	delete_custom_fields(get_sales_team_custom_fields())

def delete_custom_fields(custom_fields: dict):
	"""
	Method to Delete custom fields
	args:
		custom_fields: a dict like `{'Task': [{fieldname: 'your_fieldname', ...}]}`
	"""
	for doctype, fields in custom_fields.items():
		frappe.db.delete(
			"Custom Field",
			{
				"fieldname": ("in", [field["fieldname"] for field in fields]),
				"dt": doctype,
			},
		)
		frappe.clear_cache(doctype=doctype)

def get_purchase_order_custom_fields():
	"""
	Custom fields that need to be added to the Purchase Order DocType
	"""
	return {
		"Purchase Order": [
			{
				"fieldname": "purchase_category",
				"fieldtype": "Select",
				"label": "Purchase Category",
				"options": "Normal\nSpecial",
				"insert_after": "is_subcontracted"
			}
		]
	}

def get_purchase_receipt_custom_fields():
	"""
	Custom fields that need to be added to the Purchase Receipt DocType
	"""
	return {
		"Purchase Receipt": [
			{
				"fieldname": "purchase_category",
				"fieldtype": "Select",
				"label": "Purchase Category",
				"options": "Normal\nSpecial",
				"insert_after": "is_return"
			}
		]
	}

def get_purchase_invoice_custom_fields():
	"""
	Custom fields that need to be added to the Purchase Invoice DocType
	"""
	return {
		"Purchase Invoice": [
			{
				"fieldname": "purchase_category",
				"fieldtype": "Select",
				"label": "Purchase Category",
				"options": "Normal\nSpecial",
				"insert_after": "apply_tds"
			},
			{
				"fieldname": "purchase_schema",
				"fieldtype": "Select",
				"label": "Purchase Schema",
				"options": "Item-wise\nInvoice-level",
				"insert_after": "supplier"
			},
			{
				"fieldname": "schema_discount_amount",
				"fieldtype": "Currency",
				"label": "Schema Discount Amount",
				"insert_after": "items",
				"read_only_depends_on": "eval:doc.purchase_schema == 'Item-wise'"
			}
		]
	}

def get_purchase_invoice_item_custom_fields():
	"""
	Custom fields that need to be added to the Purchase Invoice Item DocType
	"""
	return {
		"Purchase Invoice Item": [
			{
				"fieldname": "schema_discount_amount",
				"fieldtype": "Currency",
				"label": "Schema Discount Amount",
				"insert_after": "amount"
			}
		]
	}

def get_item_custom_fields():
	"""
	Custom fields that need to be added to the Item DocType
	"""
	return {
		"Item": [
			{
				"fieldname": "sales_commission",
				"fieldtype": "Select",
				"label": "Sales Commission",
				"options": "Percentage\nFixed",
				"insert_after": "max_discount"
			},
			{
				"fieldname": "commission_value",
				"fieldtype": "Float",
				"label": "Commission Value",
				"insert_after": "sales_commission"
			},
			{
				"fieldname": "demo_required",
				"fieldtype": "Check",
				"label": "Demo Required",
				"insert_after": "allow_negative_stock"
			},
			{
				"fieldname": "periodic_service",
				"fieldtype": "Check",
				"label": "Periodic Service",
				"insert_after": "demo_required"
			},
			{
				"fieldname": "mrp",
				"fieldtype": "Float",
				"label": "MRP",
				"insert_after": "stock_uom"
			},
			{
				"fieldname": "sales_expense_contribution",
				"fieldtype": "Data",
				"label": "Sales Expense Contribution",
				"insert_after": "commission_value"
			},
		]
	}

def get_customer_custom_fields():
	"""
	Custom fields that need to be added to the Customer DocType
	"""
	return {
		"Customer": [
			{
				"fieldname": "is_provider",
				"fieldtype": "Check",
				"label": "Is Provider",
				"insert_after": "customer_group"
			}
		]
	}

def get_sales_order_item_custom_fields():
	"""
	Custom fields that need to be added to the Sales Order Item DocType
	"""
	return {
		"Sales Order Item": [
			{
				"fieldname": "allow_commission",
				"fieldtype": "Check",
				"label": "Allow Commission",
				"insert_after": "item_tax_template"
			},
			{
				"fieldname": "profit_for_commission",
				"fieldtype": "Currency",
				"label": "Profit for Commission",
				"insert_after": "allow_commission"
			}
		]
	}

def get_sales_invoice_item_custom_fields():
	"""
	Custom fields that need to be added to the Sales Invoice Item DocType
	"""
	return {
		"Sales Invoice Item": [
			{
				"fieldname": "allow_commission",
				"fieldtype": "Check",
				"label": "Allow Commission",
				"insert_after": "item_tax_template"
			},
			{
				"fieldname": "profit_for_commission",
				"fieldtype": "Currency",
				"label": "Profit for Commission",
				"insert_after": "allow_commission"
			},
			{
				"fieldname": "is_demo_reqd",
				"fieldtype": "Check",
				"label": "Demo Required",
				"fetch_from": "item_code.demo_required",
				"read_only": 1,
				"insert_after": "is_free_item"
			},
			{
				"fieldname": "sales_expense_contribution",
				"fieldtype": "Data",
				"label": "Sales Expense Contribution",
				"insert_after": "is_demo_reqd"
			}
		]
	}

def get_serial_and_batch_entry_custom_fields():
	"""
	Custom fields that need to be added to the Serial and Batch Entry DocType
	"""
	return {
		"Serial and Batch Entry": [
			{
				"fieldname": "purchase_category",
				"fieldtype": "Select",
				"label": "Purchase Category",
				"options": "\nNormal\nSpecial",
				"insert_after": "batch_no",
				"read_only": 1,
				"allow_on_submit": 1
			}
		]
	}

def get_stock_reconciliation_custom_fields():
	"""
	Custom fields that need to be added to the Stock Reconciliation DocType
	"""
	return {
		"Stock Reconciliation": [
			{
				"fieldname": "purchase_category",
				"fieldtype": "Select",
				"label": "Purchase Category",
				"options": "Normal\nSpecial",
				"insert_after": "set_posting_time"
			}
		]
	}

def get_mode_of_payment_custom_fields():
	"""
	Custom fields that need to be added to the Mode Of Payment DocType
	"""
	return {
		"Mode of Payment": [
			{
				"fieldname": "is_finance",
				"fieldtype": "Check",
				"label": "Is Finance",
				"insert_after": "enabled"
			}
		]
	}	

def get_task_custom_fields():
	"""
	Custom fields that need to be added to the Task DocType
	"""
	return {
		"Task": [
			{
				"fieldname": "section_break_l",
				"fieldtype": "Section Break",
				"label": "Invoice Details",
				"insert_after": "parent_task",
				"collapsible": 1
			},
			{
				"fieldname": "invoice_reference",
				"fieldtype": "Link",
				"label": "Sales Invoice",
				"options": "Sales Invoice",
				"read_only": 1,
				"insert_after": "section_break_l"
			},
			{
				"fieldname": "invoice_date",
				"fieldtype": "Date",
				"label": "Invoice Date",
				"read_only": 1,
				"insert_after": "invoice_reference"
			},
			{
				"fieldname": "column_break_task",
				"fieldtype": "Column Break",
				"label": " ",
				"insert_after": "invoice_date",
				"collapsible": 1
			},
			{
				"fieldname": "customer",
				"fieldtype": "Link",
				"label": "Customer",
				"options": "Customer",
				"read_only": 1,
				"insert_after": "column_break_task"
			},
		]
	}	

def create_property_setters(property_setter_datas):
	'''
	Method to create custom property setters
	args:
		property_setter_datas : list of dict of property setter obj
	'''
	for property_setter_data in property_setter_datas:
		if frappe.db.exists("Property Setter", property_setter_data):
			continue
		property_setter = frappe.new_doc("Property Setter")
		property_setter.update(property_setter_data)
		property_setter.flags.ignore_permissions = True
		property_setter.insert()

def get_property_setters():
	'''
	 specific property setters that need to be added to the DocTypes
	'''
	return [
		{
			"doctype_or_field": "DocField",
			"doc_type": "Sales Invoice Item",
			"field_name": "grant_commission",
			"property": "hidden",
			"value": 1
		},
		{
			"doctype_or_field": "DocField",
			"doc_type": "Sales Order Item",
			"field_name": "grant_commission",
			"property": "hidden",
			"value": 1
		},
		{
			"doctype_or_field": "DocField",
			"doc_type": "Sales Team",
			"field_name": "allocated_amount",
			"property": "hidden",
			"value": 1
		},
		{
			"doctype_or_field": "DocField",
			"doc_type": "Sales Team",
			"field_name": "incentives",
			"property": "hidden",
			"value": 1
		},

	]
def get_sales_invoice_custom_fields():
	"""
	Custom fields that need to be added to the Sales Invoice DocType
	"""
	return {
		"Sales Invoice": [
			{
				"fieldname": "sales_type",
				"fieldtype": "Select",
				"label": "Sales Type",
				"options": "Cash\nCredit\nEMI",
				"insert_after": "naming_series"
			},
			{
				"fieldname": "mode_of_payment",
				"fieldtype": "Link",
				"label": "Mode Of Payment",
				"options": "Mode of Payment",
				"insert_after": "customer"
			},
			{
				"fieldname": "is_buyback",
				"fieldtype": "Check",
				"label": "Is Buyback",
				"insert_after": "mode_of_payment"
			},
			{
				"fieldname": "buyback_section",
				"fieldtype": "Section Break",
				"label": "",
				"insert_after": "total_taxes_and_charges"
			},
			{
				"fieldname": "buyback_items",
				"fieldtype": "Table",
				"label": "Buyback Items",
				"options": "Buyback Item",
				"insert_after": "buyback_section",
				"depends_on": "eval:doc.is_buyback",
				"mandatory_depends_on": "eval:doc.is_buyback"
			},
			{
				"fieldname": "buyback_amount_section",
				"fieldtype": "Section Break",
				"label": "",
				"insert_after": "buyback_items",
				"depends_on": "eval:doc.is_buyback"
			},
			{
				"fieldname": "buyback_column_break",
				"fieldtype": "Column Break",
				"insert_after": "buyback_amount_section"
			},
			{
				"fieldname": "buyback_items_column_break",
				"fieldtype": "Column Break",
				"insert_after": "buyback_column_break"
			},
			{
				"fieldname": "buyback_amount",
				"fieldtype": "Currency",
				"label": "Buyback Amount",
				"insert_after": "buyback_items_column_break"
			},
			{
				"fieldname": "emi_details_section",
				"fieldtype": "Tab Break",
				"label": "EMI Details",
				"insert_after": "to_date",
				"depends_on": "eval:doc.sales_type == 'EMI'"

			},
			{
				"fieldname": "down_payment_amount",
				"fieldtype": "Currency",
				"label": "Down Payment Amount",
				"insert_after": "down_payment",
				"depends_on": "eval:doc.down_payment"
			},
			{
				"fieldname": "emi_amount",
				"fieldtype": "Currency",
				"label": "EMI AMOUNT",
				"insert_after": "down_payment_amount",
				"read_only": 1
			},
			{
				"fieldname": "emi_date",
				"fieldtype": "Date",
				"label": "EMI Start Date",
				"insert_after": "emi_amount"
			},
			{
				"fieldname": "installment_column_break",
				"fieldtype": "Column Break",
				"insert_after": "emi_date"
			},
			{
				"fieldname": "no_of_installment",
				"fieldtype": "Int",
				"label": "No Of Installment",
				"insert_after": "installment_column_break"
			},
			{
				"fieldname": "emi_duration_section",
				"fieldtype": "Section Break",
				"label": "EMI Schedule",
				"insert_after": "closing_date",
				"depends_on": "eval:doc.sales_type == 'EMI'"

			},
			{
				"fieldname": "emi_duration",
				"fieldtype": "Table",
				"label": "EMI Schedule",
				"options":"EMI Duration",
				"insert_after": "emi_duration_section",
				"read_only": 1
			},
			{
				"fieldname": "down_payment",
				"fieldtype": "Check",
				"label": "Is Down Payment",
				"insert_after": "emi_details_section"
			},
			{
				"fieldname": "down_payment_paid",
				"fieldtype": "Check",
				"label": "Down Payment Paid",
				"insert_after": "no_of_installment",
				"allow_on_submit" : 1 ,
				"read_only": 1,
			},
			{
				"fieldname": "closing_date",
				"fieldtype": "Date",
				"label": "Closing Date",
				"insert_after": "down_payment_paid",
				"read_only": 1
			},
			{
				"fieldname": "sales_expense_tab",
				"fieldtype": "Tab Break",
				"label": "Sales Expenses",
				"insert_after": "timesheets"
			},
			{
				"fieldname": "sales_expenses",
				"fieldtype": "Table",
				"label": "Sales Expenses",
				"options":"Sales Expenses",
				"insert_after": "sales_expense_tab"
			},
			{
				"fieldname": "sales_expense_sec",
				"fieldtype": "Section Break",
				"label": " ",
				"insert_after": "sales_expenses"
			},
			{
				"fieldname": "sales_expense_col",
				"fieldtype": "Column Break",
				"insert_after": "sales_expense_sec"
			},
			{
				"fieldname": "total_expense",
				"fieldtype": "Currency",
				"label": "Total Expense",
				"read_only": 1,
				"insert_after": "sales_expense_col"
			},
			{
				"fieldname": "total_commission_rate",
				"fieldtype": "Currency",
				"label": "Total Commission",
				"insert_after": "items"
			},
			{
				"fieldname": "emi_provider",
				"fieldtype": "Link",
				"options": "Customer",
				"label": "EMI Provider",
				"insert_after": "sales_type",
				"depends_on": "eval:doc.sales_type == 'EMI'"
			},
		]
	}

def get_sales_order_custom_fields():
	"""
	Custom fields that need to be added to the Sales Order Item DocType
	"""
	return {
		"Sales Order": [
			{
				"fieldname": "total_commission_rate",
				"fieldtype": "Currency",
				"label": "Total Commission",
				"insert_after": "items"
			},
		]
	}

def get_sales_team_custom_fields():
	"""
	Custom fields that need to be added to the Sales Team DocType
	"""
	return {
		"Sales Team": [
			{
				"fieldname": "total_commission_rate",
				"fieldtype": "Currency",
				"label": "Total Commission",
				"insert_after": "contact_no"
			},
			{
				"fieldname": "incentive",
				"fieldtype": "Currency",
				"label": "Incentive",
				"insert_after": "total_commission_rate"
			},
		]
	}
