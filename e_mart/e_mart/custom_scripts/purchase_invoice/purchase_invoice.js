// Copyright (c) 2025, efeone and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Invoice', {
	onload: function(frm) {
		let previous_length = frm.doc.items ? frm.doc.items.length : 0;

		frm.fields_dict.items.grid.wrapper.on('click', function() {
			setTimeout(() => {
				let current_length = frm.doc.items ? frm.doc.items.length : 0;
				if (current_length !== previous_length) {
					update_schema_discount_amount_total(frm);
					previous_length = current_length;
				}
			}, 150);
		});
	}
});

frappe.ui.form.on('Purchase Invoice Item', {
	schema_discount_amount: function(frm, cdt, cdn) {
        calculate_total_schema_discount(cdt, cdn);
        update_schema_discount_amount_total(frm);
	},
    qty: function(frm, cdt, cdn) {
         calculate_total_schema_discount(cdt, cdn);
         update_schema_discount_amount_total(frm);
    }
});

/**
 * function to calculate the total of schema discount amount from items table
 */
function update_schema_discount_amount_total(frm) {
	let total = 0;
	(frm.doc.items || []).forEach(row => {
		if (row.total_schema_discount_amount) {
			total += row.total_schema_discount_amount;
		}
	});
	frm.set_value('schema_discount_amount', total);
}

function calculate_total_schema_discount(cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.qty && row.schema_discount_amount) {
        row.total_schema_discount = row.qty * row.schema_discount_amount;
        frappe.model.set_value(cdt, cdn, 'total_schema_discount_amount', row.total_schema_discount);
    }
}
        