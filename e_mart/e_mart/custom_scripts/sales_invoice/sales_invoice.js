// frappe.ui.form.on('Sales Invoice', {
//     onload: function(frm) {
//         update_total_buyback_amount(frm);
//     }
// });

// frappe.ui.form.on('Buyback Item', {
//     qty: function(frm, cdt, cdn) {
//         calculate_row_amount(frm, cdt, cdn);
//     },
//     rate: function(frm, cdt, cdn) {
//         calculate_row_amount(frm, cdt, cdn);
//     },
//     buyback_items_remove: function(frm) {
//         update_total_buyback_amount(frm);
//     },
//     buyback_items_add: function(frm) {
//         update_total_buyback_amount(frm);
//     }
// });

// function calculate_row_amount(frm, cdt, cdn) {
//     let row = locals[cdt][cdn];
//     row.amount = (row.qty || 0) * (row.rate || 0);
//     frm.fields_dict.buyback_items.grid.refresh(); // visually refresh
//     update_total_buyback_amount(frm);
// }

// function update_total_buyback_amount(frm) {
//     let total = 0;
//     (frm.doc.buyback_items || []).forEach(row => {
//         total += row.amount || 0;
//     });
//     frm.set_value('buyback_amount', total);
// }

frappe.ui.form.on('Sales Invoice', {
    onload(frm) {
        update_total_buyback_amount(frm);
    },

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

function calculate_row_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    row.amount = (row.qty || 0) * (row.rate || 0);
    frm.fields_dict.buyback_items.grid.refresh();
    update_total_buyback_amount(frm);
}

function update_total_buyback_amount(frm) {
    let total = 0;
    (frm.doc.buyback_items || []).forEach(row => {
        total += row.amount || 0;
    });
    frm.set_value('buyback_amount', total);
}
