// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Invoice', {
	onload(frm) {
		frm.fields_dict.buyback_items.grid.wrapper.on('change', function () {
			update_total_buyback_amount(frm);
			update_rounded_total(frm);
		});
		set_customer_filter(frm);
	},
	refresh: function (frm) {
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
		}
	},
	sales_type(frm) {
		set_customer_filter(frm);
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
	},
	calculate_totals(frm) {
		setTimeout(() => {
			update_outstanding_amount(frm);
			update_rounded_total(frm);
		}, 200);
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
    },
    items_add(frm) {
        frm.trigger("calculate_totals");
    },
    items_remove(frm) {
        frm.trigger("calculate_totals");
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
}

// Calculate Outstanding Amount
function update_outstanding_amount(frm) {
    if (frm.doc.docstatus === 0) { // only allow before submit
        const total = flt(frm.doc.total || 0);
        const taxes = flt(frm.doc.total_taxes_and_charges || 0);
        const buyback = flt(frm.doc.buyback_amount || 0);

        let outstanding = total + taxes;
        if (frm.doc.is_buyback) {
            outstanding -= buyback;
        }
        frm.set_value('outstanding_amount', Math.max(outstanding, 0));
    }
}

// Calculate Rounded Total
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


// Filter customer field to show only providers when sales_type is EMI
// If selected customer is not a provider, clear it
function set_customer_filter(frm) {
	frm.set_query("customer", () => {
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

	if (frm.doc.sales_type === "EMI" && frm.doc.customer) {
		frappe.db.get_value("Customer", frm.doc.customer, "is_provider", (r) => {
			if (r && r.is_provider !== 1) {
				frm.set_value("customer", null);
			}
		});
	}
}

/**
 * Calculates the EMI amount after deducting the down payment
 * and updates the emi_amount field immediately.
 */
function update_emi_amount(frm) {
	let down_payment = frm.doc.down_payment_amount || 0;
	let total = frm.doc.total || 0;
	let emi_amount = total - down_payment;

	frm.set_value('emi_amount', emi_amount);
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
