# Copyright (c) 2025, efeone and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate
from frappe import _
from frappe.model.document import Document

class MonthlyCommissionLog(Document):
	pass

@frappe.whitelist()
def create_additional_salary_from_commission(log_name):
	log = frappe.get_doc("Monthly Commission Log", log_name)

	if not log.monthly_commission_log:
		frappe.throw("No commission details found.")

	if not log.employee:
		frappe.throw("Employee is not set in the Monthly Commission Log.")

	# Get the latest date from the child table
	latest_date = max(
		getdate(row.date) for row in log.monthly_commission_log if row.date
	)

	total_incentive = sum(row.incentives for row in log.monthly_commission_log if row.incentives)
	salary_component = frappe.db.get_single_value("E-mart Settings", "additional_salary_component")
	if not salary_component:
		frappe.throw(_("Please set the Additional Salary Component in E-mart Settings before proceeding."),title=_("Configuration Required"))

	doc = frappe.get_doc({
		"doctype": "Additional Salary",
		"employee": log.employee,
		"company": frappe.defaults.get_user_default("company"),
		"salary_component": salary_component,
		"amount": total_incentive,
		"payroll_date": latest_date,
		"overwrite_salary_structure_amount": 1
	})
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	return doc.name
