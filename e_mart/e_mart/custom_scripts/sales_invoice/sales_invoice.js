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

    // Triggered before saving or submitting the form
    // If is_buyback is checked, subtract buyback_amount from outstanding_amount
    validate(frm) {
        if (frm.doc.is_buyback && frm.doc.buyback_amount) {
            let new_outstanding = (frm.doc.outstanding_amount || 0) - frm.doc.buyback_amount;
            frm.set_value('outstanding_amount', Math.max(new_outstanding, 0));
        }
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