
import frappe

def update_down_payment_status(doc, method):
	"""
	On Payment Entry Submit:
	If fully paid down payment for Sales Invoice, mark down_payment_paid = 1.
	"""
	for ref in doc.references:
		if ref.reference_doctype == "Sales Invoice":
			si_name = ref.reference_name

			down_payment = frappe.db.get_value("Sales Invoice", si_name, "down_payment")
			down_payment_amount = frappe.db.get_value("Sales Invoice", si_name, "down_payment_amount")

			if down_payment and down_payment_amount and doc.paid_amount == down_payment_amount:
				frappe.db.set_value("Sales Invoice", si_name, "down_payment_paid", 1)

