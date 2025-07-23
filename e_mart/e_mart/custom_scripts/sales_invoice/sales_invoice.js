// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Invoice', {
	onload(frm) {
		frm.fields_dict.buyback_items.grid.wrapper.on('change', function () {
			update_total_buyback_amount(frm);
			update_rounded_total(frm);
		});
		set_finance_filter(frm);
		attach_sales_expense_grid_events(frm);
		calculate_total_expense(frm);
		update_emi_amount(frm)
	},
	refresh: function (frm) {
		if (frm.doc.docstatus === 0) {
			update_outstanding_amount(frm);
			update_rounded_total(frm);
			update_emi_amount(frm)
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
	},
	sales_type(frm) {
		set_finance_filter(frm);
	},
	// Triggered when relevant fields change for EMI recalculation
	down_payment_amount: function(frm) {
		update_emi_amount(frm);
		generate_emi_schedule(frm); 
	},
	total: function(frm) {
		update_outstanding_amount(frm);
		update_rounded_total(frm);
		update_emi_amount(frm);
		generate_emi_schedule(frm);
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
	no_of_installment: function(frm) {
		generate_emi_schedule(frm);
	},
	emi_amount: function(frm) {
		generate_emi_schedule(frm);
	},
	emi_date: function(frm) {
		generate_emi_schedule(frm);
	},
	validate(frm) {
		update_emi_amount(frm);
		generate_emi_schedule(frm);
		calculate_total_expense(frm);
        update_profit_for_commission(frm);
	},
	calculate_totals(frm) {
		setTimeout(() => {
			update_outstanding_amount(frm);
			update_rounded_total(frm);
			calculate_total_expense(frm);
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
	buyback_items_remove(frm) {
		update_total_buyback_amount(frm);
	}
});
// Sales Invoice Items child table
frappe.ui.form.on('Sales Invoice Item', {
	qty(frm) {
		frm.trigger("calculate_totals");
	},
	rate(frm) {
		frm.trigger("calculate_totals");
	},
	amount(frm) {
		frm.trigger("calculate_totals");
		calculate_total_expense(frm);
	},
	items_add(frm) {
		frm.trigger("calculate_totals");
	},
	items_remove(frm) {
		frm.trigger("calculate_totals");
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
    },
	sales_expense_contribution(frm, cdt, cdn) {
        update_profit_for_commission(frm);
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
function update_emi_amount(frm) {
    if (frm.doc.docstatus !== 0) {
		return;
	}
	const down_payment = flt(frm.doc.down_payment_amount || 0);
	const outstanding = flt(frm.doc.outstanding_amount || 0);
	const emi_amount = outstanding - down_payment;

	frm.set_value('emi_amount', Math.max(emi_amount, 0));
}


/**
 * Generates EMI Duration child table rows dynamically
 * based on customer emi_start_date, emi_amount, and no_of_installment.
 */
function generate_emi_schedule(frm) {
	let emi_date = frm.doc.emi_date;
	let no_of_installments = frm.doc.no_of_installment;
	let emi_amount = frm.doc.emi_amount;

	if (!emi_date || !no_of_installments || !emi_amount) {
		return;
	}

	frm.clear_table('emi_duration');

	let installment_amount = Number(emi_amount) / Number(no_of_installments);
	let last_date = null;

	for (let i = 0; i < Number(no_of_installments); i++) {
		let installment_date = frappe.datetime.add_months(emi_date, i);
		last_date = installment_date; // Track last date

		frm.add_child('emi_duration', {
			date: installment_date,
			amount: installment_amount
		});
	}

	frm.refresh_field('emi_duration');

	// Set closing_date to last EMI date
	if (last_date) {
		frm.set_value('closing_date', last_date);
	}
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
