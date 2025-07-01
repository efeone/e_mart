frappe.ui.form.on('Sales Invoice', {
    onload(frm) {
        update_total_buyback_amount(frm);
        set_customer_filter(frm);
    },
    refresh: function (frm) {
        if (frm.doc.docstatus === 1 && frm.doc.sales_type == "EMI") {
            frm.add_custom_button(__('Finance Invoice'), function () {
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
            }, __('Create'));
        }
    },
    sales_type(frm) {
        set_customer_filter(frm);
    },
    // If is_buyback is checked, subtract buyback_amount from outstanding_amount
    validate(frm) {
        if (frm.doc.is_buyback && frm.doc.buyback_amount) {
            let new_outstanding = (frm.doc.outstanding_amount || 0) - frm.doc.buyback_amount;
            frm.set_value('outstanding_amount', Math.max(new_outstanding, 0));
        }
    }
});

frappe.ui.form.on('Buyback Item', {
    qty(frm, cdt, cdn) {
        calculate_row_amount(frm, cdt, cdn);
    },
    rate(frm, cdt, cdn) {
        calculate_row_amount(frm, cdt, cdn);
    },
    buyback_items_add(frm) {
        update_total_buyback_amount(frm);
    },
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
