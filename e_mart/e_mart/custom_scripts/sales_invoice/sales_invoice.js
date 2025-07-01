// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Invoice', {
    // Triggered when the form is loaded
    onload(frm) {
        update_total_buyback_amount(frm);
        set_customer_filter(frm);
    },

    // Triggered when the sales_type field is changed
    sales_type(frm) {
        set_customer_filter(frm);
    },
    // Triggered when relevant fields change for EMI recalculation
    down_payment_amount: function(frm) {
        update_emi_amount(frm);
        generate_emi_schedule(frm); 
    },
    total: function(frm) {
        update_emi_amount(frm);
        generate_emi_schedule(frm);
    },
    no_of_installment: function(frm) {
        generate_emi_schedule(frm);
    },
    emi_amount: function(frm) {
        generate_emi_schedule(frm);
    },
    customer: function(frm) {
        generate_emi_schedule(frm);
    },

    // Triggered before saving or submitting the form
    // If is_buyback is checked, subtract buyback_amount from outstanding_amount
    validate(frm) {
        if (frm.doc.is_buyback && frm.doc.buyback_amount) {
            let new_outstanding = (frm.doc.outstanding_amount || 0) - frm.doc.buyback_amount;
            frm.set_value('outstanding_amount', Math.max(new_outstanding, 0));
        }
        update_emi_amount(frm);
        generate_emi_schedule(frm);
    }
});

frappe.ui.form.on('Buyback Item', {
    // Recalculate amount when quantity is changed
    qty(frm, cdt, cdn) {
        calculate_row_amount(frm, cdt, cdn);
    },

    // Recalculate amount when rate is changed
    rate(frm, cdt, cdn) {
        calculate_row_amount(frm, cdt, cdn);
    },

    // Update total buyback amount when a new row is added
    buyback_items_add(frm) {
        update_total_buyback_amount(frm);
    },

    // Update total buyback amount when a row is removed
    buyback_items_remove(frm) {
        update_total_buyback_amount(frm);
    }
});

// Calculate the amount for the Buyback Item row
// and update the total buyback amount
function calculate_row_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    row.amount = (row.qty || 0) * (row.rate || 0);
    frm.fields_dict.buyback_items.grid.refresh();
    update_total_buyback_amount(frm);
}

// Sum all row amounts from buyback_items
// and set the parent field buyback_amount
function update_total_buyback_amount(frm) {
    let total = 0;
    (frm.doc.buyback_items || []).forEach(row => {
        total += row.amount || 0;
    });
    frm.set_value('buyback_amount', total);
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
    let customer = frm.doc.customer;
    let no_of_installments = frm.doc.no_of_installment;
    let emi_amount = frm.doc.emi_amount;

    if (!customer || !no_of_installments || !emi_amount) {
        return;
    }

    frappe.db.get_doc('Customer', customer)
        .then(doc => {
            let emi_start_date = doc.emi_start_date;
            if (!emi_start_date) {
                return; 
            }

            frm.clear_table('emi_duration');

            let installment_amount = Number(emi_amount) / Number(no_of_installments);

            for (let i = 0; i < Number(no_of_installments); i++) {
                let installment_date = frappe.datetime.add_months(emi_start_date, i);
                frm.add_child('emi_duration', {
                    date: installment_date,
                    amount: installment_amount
                });
            }

            frm.refresh_field('emi_duration');
        });
}
