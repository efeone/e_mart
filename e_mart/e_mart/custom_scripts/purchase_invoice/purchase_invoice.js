frappe.ui.form.on('Purchase Invoice Item', {
    schema_discount_amount: function(frm) {
        let total = 0;
        frm.doc.items.forEach(function(row) {
            if (row.schema_discount_amount) {
                total += row.schema_discount_amount;
            }
        });
        frm.set_value('schema_discount_amount', total);
    }
});


