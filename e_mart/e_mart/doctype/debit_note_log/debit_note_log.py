# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DebitNoteLog(Document):
	def on_submit(self):
		if self.workflow_state == "Approved":
			self.create_journal_entry()

	def on_update(self):
		self.sync_status_with_workflow()
	
	def create_journal_entry(self):
		'''
		Creates a Journal Entry for the discounted amount in the Debit Note Log
		'''
		if not self.discounted_amount or self.discounted_amount <= 0:
			frappe.throw("Discounted Amount must be greater than 0.")

		company = frappe.db.get_value("Purchase Invoice", self.purchase_invoice, "company")

		if not company:
			frappe.throw(f"Company not found for Purchase Invoice {self.purchase_invoice}")

		supplier_account = frappe.db.get_value(
			"Party Account",
			{
				"parent": self.supplier,
				"parenttype": "Supplier",
				"company": company
			},
			"account"
		)

		if not supplier_account:
			frappe.throw(f"No account found for Supplier {self.supplier} in company {company}")

		adjusted_account = frappe.db.get_single_value("E-mart Settings", "debit_note_adjusted_account")
		if not adjusted_account:
			frappe.throw("Please set 'Debit Note Adjusted Account' in Lavanya Emart Settings.")

		# Create Journal Entry
		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Debit Note"
		je.posting_date = frappe.utils.nowdate()
		je.company = company
		je.remark = f"Auto-created from Debit Note Log {self.name} for Purchase Invoice {self.purchase_invoice}"

		# Debit Supplier
		je.append("accounts", {
			"account": supplier_account,
			"party_type": "Supplier",
			"party": self.supplier,
			"debit_in_account_currency": self.discounted_amount,
			"reference_type": "Purchase Invoice",
			"reference_name": self.purchase_invoice
		})

		# Credit Adjusted Account
		je.append("accounts", {
			"account": adjusted_account,
			"credit_in_account_currency": self.discounted_amount
		})

		je.insert(ignore_permissions=True)
		je.submit()

		if frappe.get_meta(self.doctype).has_field("jv_reference"):
			self.db_set("jv_reference", je.name)

		frappe.msgprint(f"Journal Entry <a href='/app/journal-entry/{je.name}'>{je.name}</a> created.")

	def sync_status_with_workflow(self):
		"""
		Sync the `status` field with the current `workflow_state` on update.
		"""
		mapping = {
			"Approved": "Submitted",
			"Rejected": "Rejected",
			"Cancelled": "Cancelled",
		}

		new_status = mapping.get(self.workflow_state)

		if new_status and self.status != new_status:
			self.db_set("status", new_status)
