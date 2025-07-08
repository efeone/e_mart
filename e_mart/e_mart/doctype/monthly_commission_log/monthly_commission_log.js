// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Monthly Commission Log', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Additional Salary'), function() {
				frappe.call({
					method: 'e_mart.e_mart.doctype.monthly_commission_log.monthly_commission_log.create_additional_salary_from_commission',
					args: {
						log_name: frm.doc.name
					},
					callback: function(r) {
						if (!r.exc && r.message) {
							frappe.set_route("Form", "Additional Salary", r.message);
						}
					}
				});
			}, __('Create'));
		}
	}
});
