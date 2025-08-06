// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Invoice', {
	onload(frm) {
		frm.fields_dict.buyback_items.grid.wrapper.on('change', function () {
			update_total_buyback_amount(frm);
			update_rounded_total(frm);
		});
		frm.set_query('item', 'buyback_items', function(doc, cdt, cdn) {
			return {
				filters: {
					buyback_item: 1
				}
			};
		});
		set_finance_filter(frm);
		attach_sales_expense_grid_events(frm);
		calculate_total_expense(frm);
		calculate_total_down_payment(frm);
		update_down_payment_checkbox(frm);
		calculate_total_emi_amount(frm);
	},
	refresh: function (frm) {
		setTimeout(() => {
			frm.remove_custom_button('Payment', 'Create');
			if (frm.doc.docstatus === 1 && flt(frm.doc.outstanding_amount) > 0) {
				frm.add_custom_button(__('Payment'), function() {
					show_payment_popup(frm);
				}, __('Create'));
			}
		}, 100);
		if (frm.doc.docstatus === 0) {
			update_outstanding_amount(frm);
			update_rounded_total(frm);
		}
		if (!frm.is_new() && frm.doc.sales_type === "EMI") {
			frm.add_custom_button(__('Create Finance Invoice'), function () {
				frappe.call({
					method: "e_mart.e_mart.custom_scripts.sales_invoice.sales_invoice.create_finance_invoice",
					args: {
						sales_invoice_name: frm.doc.name
					},
					callback: function (r) {
						if (r.message) {
							frappe.set_route('Form', 'Finance Invoice', r.message);
						}
					}
				});
			});
			if (frm.doc.docstatus === 1 && frm.doc.down_payment && frm.doc.down_payment_amount && frm.doc.down_payment_paid == 0 ) {
				frm.add_custom_button(__('Down Payment'), function() {
					frappe.model.open_mapped_doc({
						method: "e_mart.e_mart.custom_scripts.sales_invoice.sales_invoice.make_down_payment_entry",
						source_name: frm.doc.name
					});
				}, __('Create'));
			}
		}
		calculate_total_expense(frm);
		calculate_total_down_payment(frm);
		update_down_payment_checkbox(frm);
		calculate_total_emi_amount(frm);
	},
	sales_type(frm) {
		set_finance_filter(frm);
		sync_sales_type_to_items(frm);
	},
	total: function(frm) {
		update_outstanding_amount(frm);
		update_rounded_total(frm);
	},
	total_taxes_and_charges(frm) {
		update_outstanding_amount(frm);
		update_rounded_total(frm);
	},

	buyback_amount(frm) {
		update_outstanding_amount(frm);
		update_rounded_total(frm);
	},

	is_buyback(frm) {
		update_outstanding_amount(frm);
		update_rounded_total(frm);
	},
	validate(frm) {
		calculate_total_expense(frm);
		update_profit_for_commission(frm);
		calculate_total_down_payment(frm);
		calculate_total_emi_amount(frm);
	},
	calculate_totals(frm) {
		setTimeout(() => {
			update_outstanding_amount(frm);
			update_rounded_total(frm);
			calculate_total_expense(frm);
			calculate_total_down_payment(frm);
			calculate_total_emi_amount(frm);
		}, 200);
	},
	total_expense(frm) {
		update_profit_for_commission(frm);
	}
});
// Buyback Item child table
frappe.ui.form.on('Buyback Item', {
	qty(frm, cdt, cdn) {
		calculate_row_amount(frm, cdt, cdn);
	},
	rate(frm, cdt, cdn) {
		calculate_row_amount(frm, cdt, cdn);
	},
	buyback_items_add(frm) {
		update_total_buyback_amount(frm);
		update_grand_total(frm);
		update_rounded_total(frm);
		update_outstanding_amount(frm)
	},
	buyback_items_remove(frm) {
		update_total_buyback_amount(frm);
		update_grand_total(frm);
		update_rounded_total(frm);
		update_outstanding_amount(frm)
	}
});
// Sales Invoice Items child table
frappe.ui.form.on('Sales Invoice Item', {
	qty(frm, cdt, cdn) {
		frm.trigger("calculate_totals");
		update_emi_amount(frm, cdt, cdn);
		set_valuation_and_gross_profit(frm, cdt, cdn);
	},
	rate(frm, cdt, cdn) {
		frm.trigger("calculate_totals");
		update_emi_amount(frm, cdt, cdn);
		set_valuation_and_gross_profit(frm, cdt, cdn);
	},
	amount(frm, cdt, cdn) {
		frm.trigger("calculate_totals");
		calculate_total_expense(frm);
		update_emi_amount(frm, cdt, cdn);
	},
	down_payment(frm, cdt, cdn) {
		update_emi_amount(frm, cdt, cdn);
		calculate_total_down_payment(frm);
	},
	is_down_payment(frm, cdt, cdn) {
		update_down_payment_checkbox(frm);
	},
	emi_amount(frm, cdt, cdn) {
		calculate_total_emi_amount(frm);
	},
	items_add(frm) {
		frm.trigger("calculate_totals");
		update_down_payment_checkbox(frm);
	},
	items_remove(frm) {
		frm.trigger("calculate_totals");
		calculate_total_down_payment(frm);
		update_down_payment_checkbox(frm);
		calculate_total_emi_amount(frm);
	},
	item_code(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.item_code) {
			frappe.db.get_value("Item", row.item_code, "sales_expense_contribution")
			.then(r => {
				if (r.message) {
					frappe.model.set_value(cdt, cdn, "sales_expense_contribution", r.message.sales_expense_contribution);
					update_profit_for_commission(frm);
					}
				});
			}
			set_valuation_and_gross_profit(frm, cdt, cdn);
	},
	sales_expense_contribution(frm, cdt, cdn) {
		update_profit_for_commission(frm);
	},
	form_render: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		row.sales_type = frm.doc.sales_type;
		refresh_field("items");
	}
});

// Taxes child table
frappe.ui.form.on('Sales Taxes and Charges', {
	tax_amount(frm) {
		frm.trigger("calculate_totals");
	},
	rate(frm) {
		frm.trigger("calculate_totals");
	},
	taxes_add(frm) {
		frm.trigger("calculate_totals");
	},
	taxes_remove(frm) {
		frm.trigger("calculate_totals");
	}
});

// Calculate Buyback Row Amount
function calculate_row_amount(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	row.amount = (flt(row.qty) || 0) * (flt(row.rate) || 0);
	frm.fields_dict.buyback_items.grid.refresh();
	update_total_buyback_amount(frm);
}

// Sum all row amounts from buyback_items_amount
function update_total_buyback_amount(frm) {
	let total = 0;
	(frm.doc.buyback_items || []).forEach(row => {
		total += flt(row.amount || 0);
	});
	frm.set_value('buyback_amount', total);
	update_outstanding_amount(frm);
	update_rounded_total(frm);
	update_grand_total(frm);
}

/*
* Calculate Outstanding Amount based on buyback amount
*/
function update_outstanding_amount(frm) {
	if (frm.doc.docstatus === 0) { 
		const total = flt(frm.doc.total || 0);
		const taxes = flt(frm.doc.total_taxes_and_charges || 0);
		const buyback = flt(frm.doc.buyback_amount || 0);

		let outstanding = total + taxes;
		if (frm.doc.is_buyback) {
			outstanding -= buyback;
		}
		frm.set_value('outstanding_amount', Math.max(outstanding, 0));
		update_grand_total(frm); 
		update_emi_amount(frm);
	}
}

/*
* Calculate Rounded Total based on buyback amount
*/
function update_rounded_total(frm) {
	const total = flt(frm.doc.total || 0);
	const taxes = flt(frm.doc.total_taxes_and_charges || 0);
	const buyback = flt(frm.doc.buyback_amount || 0);

	let grand_total = total + taxes;
	if (frm.doc.is_buyback) {
		grand_total -= buyback;
	}
	frm.set_value('rounded_total', Math.round(grand_total));
}

/*
* Calculate Grand Total based on buyback amount
*/
function update_grand_total(frm) {
	const total = flt(frm.doc.total || 0);
	const taxes = flt(frm.doc.total_taxes_and_charges || 0);
	const buyback = flt(frm.doc.buyback_amount || 0);

	let grand_total = total + taxes;
	if (frm.doc.is_buyback) {
		grand_total -= buyback;
	}
	frm.set_value('grand_total', grand_total);
}

// Filter customer field to show only providers when sales_type is EMI
// If selected customer is not a provider, clear it
function set_finance_filter(frm) {
	frm.set_query("mode_of_payment", () => {
		if (frm.doc.sales_type === "EMI") {
			return {
				filters: {
					is_finance: 1
				}
			};
		} else {
			return {};
		}
	});

	frm.set_query("emi_provider", () => {
		if (frm.doc.sales_type === "EMI") {
			return {
				filters: {
					is_provider: 1
				}
			};
		} else {
			return {};
		}
	});
}

/**
 * Calculates the EMI amount after deducting the down payment
 * and updates the emi_amount field immediately.
 */
function update_emi_amount(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (frm.doc.docstatus !== 0) {
		return;
	}
	const down_payment = flt(row.down_payment || 0);
	const total_amount = flt(row.amount || 0);
	const emi_amount = total_amount - down_payment;

	frappe.model.set_value(cdt, cdn, 'emi_amount', Math.max(emi_amount, 0));
}

frappe.ui.form.on('Sales Expenses', {
	amount(frm, cdt, cdn) {
		calculate_total_expense(frm);
	},
	sales_expenses_add(frm) {
		calculate_total_expense(frm);
	},
	sales_expenses_remove(frm) {
		calculate_total_expense(frm);
	}
});

/**
 * Attach grid-remove-row event to Sales Expenses child table.
 */
function attach_sales_expense_grid_events(frm) {
	if (frm._sales_expense_grid_attached) return;

	frm.fields_dict['sales_expenses'].grid.wrapper.on('grid-remove-row', () => {
		calculate_total_expense(frm);
	});

	frm._sales_expense_grid_attached = true;
}

/**
 * Sum up all amounts in Sales Expenses child table
 * and update total_expense field.
 */
function calculate_total_expense(frm) {
	let total = 0;

	(frm.doc.sales_expenses || []).forEach(row => {
		total += flt(row.amount || 0);
	});
	frm.set_value('total_expense', total);
	update_profit_for_commission(frm);
}

frappe.ui.form.on("Sales Team", {
	allocated_percentage: function(frm, cdt, cdn) {
			var sales_person = frappe.get_doc(cdt, cdn);
			let row = locals[cdt][cdn];
			if (sales_person.allocated_percentage) {
				sales_person.allocated_percentage = sales_person.allocated_percentage;
				sales_person.total_commission_rate = frm.doc.total_commission_rate;
				sales_person.incentive = flt(
					(sales_person.total_commission_rate * row.allocated_percentage) / 100.0,
				);
				frm.refresh_field('sales_team');
			}
	}
});

/**
 * Calculates the profit for Commission for each item by subtracting its Sales Expense Contribution
 * from the total expense.
 */
function update_profit_for_commission(frm) {
	const total_expense = flt(frm.doc.total_expense || 0);

	(frm.doc.items || []).forEach(row => {
		const contribution = flt(row.sales_expense_contribution || 0);
		const profit = total_expense - contribution;
		// Set profit_for_commission for each item
		frappe.model.set_value(row.doctype, row.name, 'profit_for_commission', profit);
	});

	frm.refresh_field('items');
}

/**
 * Synchronizes the 'sales_type' field from the main Sales Invoice
 * to all child rows in the items table
 */
function sync_sales_type_to_items(frm) {
	(frm.doc.items || []).forEach(row => {
		row.sales_type = frm.doc.sales_type;
	});
	frm.refresh_field("items");
}

/**
 * Calculates and sets the total down payment amount on the invoice
 * by summing up all 'down_payment' values from the items table.
 */
function calculate_total_down_payment(frm) {
	let total = 0;
	(frm.doc.items || []).forEach(item => {
		if (item.down_payment) {
			total += item.down_payment;
		}
	});
	frm.set_value('down_payment_amount', total);
}

/**
 * Updates the 'down_payment' checkbox on the Sales Invoice.
 * It is set to true (1) if any item row has 'is_down_payment' checked.
 */
function update_down_payment_checkbox(frm) {
	let has_down_payment = (frm.doc.items || []).some(item => item.is_down_payment);
	frm.set_value('down_payment', has_down_payment ? 1 : 0);
}

/**
 * Calculates and sets the total emi amount on the invoice
 * by summing up all 'emi_amount' values from the items table.
 */
function calculate_total_emi_amount(frm) {
	let total = 0;
	(frm.doc.items || []).forEach(item => {
		if (item.emi_amount) {
			total += item.emi_amount;
		}
	});
	frm.set_value('emi_amount', total);
}
/**
 * Fetches the valuation rate from the 'Bin' table based on the item and warehouse,
 * and calculates gross profit per item. 
 */
function set_valuation_and_gross_profit(frm, cdt, cdn) {
	const row = locals[cdt][cdn];

	if (row.item_code && row.warehouse) {
		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				doctype: 'Bin',
				filters: {
					item_code: row.item_code,
					warehouse: row.warehouse
				},
				fieldname: ['valuation_rate']
			},
			callback: function(r) {
				if (r.message) {
					const valuation_rate = flt(r.message.valuation_rate);
					frappe.model.set_value(cdt, cdn, 'valuation_rate', valuation_rate);

					if (row.rate) {
						const gross_profit = (row.rate - valuation_rate) * row.qty;
						frappe.model.set_value(cdt, cdn, 'gross_profit', gross_profit);
					}
				}
			}
		});
	}
}
/**
 * Opens a popup to record multiple payments for the Sales Invoice.
 * Dynamically updates balance and creates a Payment Entry on submission.
 */
function show_payment_popup(frm) {
	let outstanding_amount = frm.doc.outstanding_amount || 0;

	const dialog = new frappe.ui.Dialog({
		title: 'Record Payment',
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'amount_summary_display',
				options: `
					<div style="display: flex; justify-content: space-between; gap: 20px; margin-bottom: 10px;">
						<div id="outstanding_amount_box" style="font-size: 16px; font-weight: bold;">
							Outstanding Amount: ₹${outstanding_amount.toFixed(2)}
						</div>
						<div id="balance_to_pay_display" style="font-size: 16px; font-weight: bold;">
							Balance to Pay: ₹${outstanding_amount.toFixed(2)}
						</div>
					</div>`
			},
			{
				fieldname: 'payments',
				fieldtype: 'Table',
				label: 'Payments',
				cannot_add_rows: false,
				in_place_edit: true,
				data: [],
				get_data: () => {
					return dialog.get_value('payments') || [];
				},
				fields: [
					{
						fieldname: 'mode_of_payment',
						fieldtype: 'Link',
						label: 'Mode of Payment',
						options: 'Mode of Payment',
						in_list_view: 1,
						reqd: 1
					},
					{
						fieldname: 'reference_no',
						fieldtype: 'Data',
						label: 'Reference No',
						in_list_view: 1
					},
					{
						fieldname: 'reference_date',
						fieldtype: 'Date',
						label: 'Reference Date',
						in_list_view: 1
					},
					{
						fieldname: 'amount',
						fieldtype: 'Currency',
						label: 'Amount',
						in_list_view: 1,
						reqd: 1
					}
				]
			}
		],
		primary_action_label: 'Submit Payment',
		primary_action(values) {
			const payments = values.payments || [];
			if (!payments.length) {
				frappe.msgprint(__('Please add at least one payment'));
				return;
			}

			frappe.call({
				method: 'e_mart.e_mart.custom_scripts.sales_invoice.sales_invoice.make_payment_entry',
				args: {
					sales_invoice: frm.doc.name,
					payments: payments
				},
				callback: function (r) {
					if (r.message) {
						frappe.msgprint('Payment Entry Created: ' + r.message);
						dialog.hide();
						frm.reload_doc();
					}
				}
			});
		}
	});

	dialog.show();
	const update_balance = () => {
		const data = dialog.get_value('payments') || [];
		const total_paid = data.reduce((acc, row) => acc + (parseFloat(row.amount) || 0), 0);
		const balance = outstanding_amount - total_paid;

		dialog.fields_dict.amount_summary_display.$wrapper
			.find('#balance_to_pay_display')
			.html(`Balance to Pay: ₹${balance.toFixed(2)}`);
	};
	frappe.realtime.on('editable_table_changed', () => {
		update_balance();
	});

	dialog.fields_dict.payments.grid.wrapper.on('input', function () {
		update_balance();
	});

	dialog.fields_dict.payments.grid.wrapper.on('click', '.grid-add-row', () => {
		setTimeout(() => {
			const grid = dialog.fields_dict.payments.grid;
			const all_rows = grid.get_data();

			let paid_so_far = 0;
			all_rows.forEach(row => {
				paid_so_far += flt(row.amount || 0);
			});

			const remaining = flt(frm.doc.outstanding_amount) - paid_so_far;

			const last_row = grid.grid_rows[grid.grid_rows.length - 1];
			if (last_row && remaining > 0) {
				frappe.model.set_value(
					last_row.doc.doctype,
					last_row.doc.name,
					'amount',
					remaining
				);
			}

			update_balance();
		}, 100);
	});
	update_balance();
}
