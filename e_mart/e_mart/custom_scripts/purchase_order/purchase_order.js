frappe.ui.form.on('Purchase Order', {
	//clears taxes and recalculates totals when Purchase Category is set to "Special"
	purchase_category: function(frm) {
		if (frm.doc.purchase_category === 'Special') {
			frm.set_value('taxes_and_charges', null);
			
			frm.clear_table('taxes');
			frm.refresh_field('taxes');
			
			frm.doc.total_taxes_and_charges = 0;
			frm.doc.taxes_and_charges_added = 0;
			frm.doc.grand_total = frm.doc.net_total || 0;
			frm.doc.rounded_total = Math.round(frm.doc.grand_total || 0);
			frm.doc.outstanding_amount = frm.doc.rounded_total || 0;
			
			frm.refresh_field('total_taxes_and_charges');
			frm.refresh_field('grand_total');
			frm.refresh_field('rounded_total');
		}
	},
	validate: function(frm) {
		if (frm.doc.purchase_category === 'Special') {
			frm.set_value('taxes_and_charges', null);
			frm.clear_table('taxes');
			frm.refresh_field('taxes');

			frm.doc.total_taxes_and_charges = 0;
			frm.doc.taxes_and_charges_added = 0;
			frm.doc.grand_total = frm.doc.net_total || 0;
			frm.doc.rounded_total = Math.round(frm.doc.grand_total || 0);

			frm.refresh_field('total_taxes_and_charges');
			frm.refresh_field('grand_total');
			frm.refresh_field('rounded_total');
		}
	}
});