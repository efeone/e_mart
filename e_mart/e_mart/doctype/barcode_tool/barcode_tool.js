// Copyright (c) 2025
// For license information, please see license.txt

frappe.ui.form.on("Barcode Tool", {
    refresh(frm) {
        // Disable save and replace with Preview & Print
        frm.disable_save();
        frm.page.set_primary_action(__('Preview & Print Barcodes'), () => {
            open_barcode_preview(frm);
        });
        // Add "Get Items From" menu
        frm.page.add_inner_button(__('Purchase Receipt'), function () {
            get_items_from_documents(frm, "Purchase Receipt");
        }, __('Get Items From'));

        frm.page.add_inner_button(__('Purchase Invoice'), function () {
            get_items_from_documents(frm, "Purchase Invoice");
        }, __('Get Items From'));

        frm.page.add_inner_button(__('Purchase Order'), function () {
            get_items_from_documents(frm, "Purchase Order");
        }, __('Get Items From'));
    },

    purchase_document(frm) {
        if (!frm.doc.purchase_document) return;

        frappe.call({
            method: "e_mart.e_mart.doctype.barcode_tool.barcode_tool.fetch_items_from_purchase",
            args: { purchase_doc: frm.doc.purchase_document },
            callback(r) {
                if (!r.message) return;

                frm.clear_table("item_table");

                r.message.forEach(item => {
                    let row = frm.add_child("item_table", {
                        items: item.item_code,
                        item_name: item.item_name,
                        barcode_qty: item.qty
                    });

                    // Fetch rendered barcode
                    frappe.call({
                        method: "e_mart.e_mart.doctype.barcode_tool.barcode_tool.render_item_barcode",
                        args: { item_code: item.item_code },
                        callback(bar) {
                            if (bar.message) {
                                row.rendered_barcode = bar.message;
                                frm.refresh_field("item_table");
                            }
                        }
                    });
                });

                frm.refresh_field("item_table");
            }
        });
    },

    item_table_add(frm) {
        frm.refresh_field("item_table");
    },

    item_table_remove(frm) {
        frm.refresh_field("item_table");
    }
});

frappe.ui.form.on("Barcode List", {
    items(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.items) return;

        frappe.call({
            method: "frappe.client.get",
            args: { doctype: "Item", name: row.items },
            callback(r) {
                if (!r.message) {
                    frappe.msgprint(`Item ${row.items} not found`);
                    return;
                }

                row.item_name = r.message.item_name;

                // Fetch rendered barcode for manual entry
                frappe.call({
                    method: "e_mart.e_mart.doctype.barcode_tool.barcode_tool.render_item_barcode",
                    args: { item_code: row.items },
                    callback(bar) {
                        if (bar.message) {
                            row.rendered_barcode = bar.message;
                            frm.refresh_field("item_table");
                        }
                    }
                });

                frm.refresh_field("item_table");
            }
        });
    },

    barcode_qty(frm) {
        frm.refresh_field("item_table");
    }
});

async function open_barcode_preview(frm) {
    if (!frm.doc.item_table?.length) {
        frappe.msgprint("No items selected for barcode generation");
        return;
    }

    try {
        const results = await Promise.all(frm.doc.item_table.map(row => render_barcode_row(row)));

        const previewWindow = window.open('', '_blank');
        previewWindow.document.write(build_preview_html(results.join('')));
        previewWindow.document.close();

    } catch (err) {
        frappe.msgprint("Error generating preview: " + err);
    }
}

function render_barcode_row(row) {
    return new Promise((resolve, reject) => {
        if (!row.items) return resolve('');

        const copies = row.barcode_qty || 1;

        // If barcode is already cached
        if (row.rendered_barcode) {
            return resolve(generate_barcode_html(row.rendered_barcode, copies));
        }

        // Otherwise fetch it
        frappe.call({
            method: "e_mart.e_mart.doctype.barcode_tool.barcode_tool.render_item_barcode",
            args: { item_code: row.items },
            callback(r) {
                if (r.message) {
                    resolve(generate_barcode_html(r.message, copies));
                } else {
                    resolve('');
                }
            },
            error: reject
        });
    });
}

function generate_barcode_html(barcode, copies) {
    return Array(copies).fill(`<div class="barcode-item">${barcode}</div>`).join('');
}

function build_preview_html(content) {
    return `
        <html>
            <head>
                <title>Barcode Preview</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 5px; }

                    .barcode-container {
                        display: flex;
                        flex-wrap: wrap;
                        width: 38mm; /* 1 cards per row */
                    }

                    .barcode-item {
                        width: 38mm;
                        height: 25mm;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        text-align: center;
                        margin: 0;
                        padding: 2px;
                        overflow: hidden;
                        box-sizing: border-box;
                        page-break-inside: avoid;
                    }

                    .barcode-content {
                        width: 100%;
                        height: 100%;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        overflow: hidden;
                    }

                    .barcode-content img,
                    .barcode-content svg {
                        max-width: 100%;
                        max-height: 60%; /* give space for text below */
                        object-fit: contain;
                    }

                    .barcode-content div,
                    .barcode-content span {
                        font-size: 9px; /* small enough to fit */
                        line-height: 1.1;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    }
                    .toolbar { text-align: center; margin-bottom: 10px; }
                    @media print {
                        .toolbar { display: none; }
                        body { margin: 0; }
                        @page { size: auto; margin: 0; } /* roll printer style */
                    }
                </style>
            </head>
            <body>
                <div class="toolbar no-print">
                    <button onclick="window.print()" style="
                        padding: 6px 12px;
                        background: #000022;
                        border: none;
                        color: white;
                        border-radius: 6px;
                        cursor: pointer;">
                        <i class="fa fa-print"></i> Print
                    </button>
                </div>
                <div class="barcode-container">${content}</div>
            </body>
        </html>
    `;
}

function get_items_from_documents(frm, doctype) {
    new frappe.ui.form.MultiSelectDialog({
        doctype: doctype,
        target: frm,
        setters: {
            supplier: frm.doc.supplier || undefined
        },
        get_query() {
            return { filters: { docstatus: 1 } };
        },
        action(selections) {
            if (selections && selections.length) {
                frappe.call({
                    method: "e_mart.e_mart.doctype.barcode_tool.barcode_tool.fetch_items_from_documents",
                    args: {
                        doctype: doctype,
                        docnames: selections
                    },
                    callback: function (r) {
                        if (r.message) {
                            frm.clear_table("item_table");
                            r.message.forEach(item => {
                                let row = frm.add_child("item_table", {
                                    items: item.item_code,
                                    item_name: item.item_name,
                                    barcode_qty: item.qty
                                });

                                // Fetch rendered barcode same as old method
                                frappe.call({
                                    method: "e_mart.e_mart.doctype.barcode_tool.barcode_tool.render_item_barcode",
                                    args: { item_code: item.item_code },
                                    callback(bar) {
                                        if (bar.message) {
                                            row.rendered_barcode = bar.message;
                                            frm.refresh_field("item_table");
                                        }
                                    }
                                });
                            });
                            frm.refresh_field("item_table");
                        }
                    }
                });
            }
            this.dialog.hide();
        }
    }); 
}
