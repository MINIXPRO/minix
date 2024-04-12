
frappe.ui.form.on('Purchase Invoice', {
    onload: function(frm) {
        frappe.call({
            method: 'minix.minix.overrides.purchase_invoice.check_suplier_multiple_tds',
            args: {
                supplier: frm.doc.supplier,
            },
            freeze: true,
            callback: r => {
                if (r.message) {
                    frm.set_value("cnp_multi_tsd", r.message);
                    frm.refresh_field("taxes_and_charges_overide")
                    frm.refresh_field("cnp_multi_tsd")
                }
            }
        })
    },
    refresh: frm => {
        set_read_only(frm)
        if (frm.doc.items) {
            if (frm.doc.items[0].purchase_receipt) {
                frappe.call({
                    method: 'minix.minix.methods.purchase_invoice.get_due_date_based_on_condition',
                    args: { pr: frm.doc.items[0].purchase_receipt },
                    freeze: true,
                    callback: r => {
                        if (r.message.due_date) {
                            frm.set_df_property('cnp_section_break_wob2z', 'hidden', true);
                        }
                        else if (r.message.status) {
                            frm.set_df_property('cnp_section_break_wob2z', 'hidden', false);
                        }
                        else {
                            frm.set_df_property('cnp_section_break_wob2z', 'hidden', true);
                        }
                    }
                })

            }
            else {
                frm.set_df_property('cnp_section_break_wob2z', 'hidden', true);
            }
        }
    },
    before_save: frm => {
        if (frm.doc.items) {
            if (frm.doc.items[0].purchase_receipt) {
                frappe.call({
                    method: 'minix.minix.methods.purchase_invoice.get_due_date_based_on_condition',
                    args: { pr: frm.doc.items[0].purchase_receipt },
                    freeze: true,
                    callback: r => {
                        if (r.message.due_date) {
                            frm.doc.payment_schedule[0].due_date = r.message.due_date;
                            frm.doc.due_date = r.message.due_date;
                        }
                        else if (r.message.status) {
                            let installation_date = frm.doc.cnp_installation_date
                            let expected_installation_date = frm.doc.cnp_expected_installation_date
                            if (frm.doc.cnp_is_installed && installation_date) {
                                frm.doc.payment_schedule[0].due_date = installation_date;
                                frm.doc.due_date = installation_date;
                            }
                            else if (!frm.doc.cnp_is_installed && expected_installation_date) {
                                frm.doc.payment_schedule[0].due_date = expected_installation_date;
                                frm.doc.due_date = expected_installation_date;
                            }
                        }

                    }
                })
            }

        }
        if (frm.doc.taxes && frm.doc.apply_tds && frm.doc.cnp_multi_tsd && frm.doc.taxes_and_charges_overide) {
            frm.doc.taxes.forEach(element => {
                if (element.rate != 0 && element.add_deduct_tax == "Deduct") {

                    element.tax_amount = (element.rate * element.base_amount) / 100
                    element.total = element.base_amount - element.tax_amount
                }
            })
            frm.refresh_field('taxes');
        }

        frappe.call({
            method: 'minix.minix.overrides.purchase_invoice.get_item_wise_tax_rcm',
            args: {
                taxes_and_charges: frm.doc.taxes_and_charges,
                items: frm.doc.items
            },
            freeze: true,
            callback: r => {

                if (!r.exc && r.message) {
                    if (frm.doc.taxes) {
                        let lastTotal = 0;
                        if (frm.doc.taxes.length > 0) {
                            lastTotal = frm.doc.taxes[frm.doc.taxes.length - 1].total;
                        }
        
                        r.message.forEach(tax => {
                            let tax_amount = tax.tax_amount_after_discount_amount;
                            tax.total = flt(lastTotal + tax_amount, 2);
                            lastTotal = tax.total;
        
                            const existingRow = frm.doc.taxes.find(row => row.account_head === tax.account_head);
        
                            if (!existingRow) {
                                frm.add_child("taxes", tax);
                            } 
                            else {
                                const existingRowIndex = frm.doc.taxes.findIndex(row => row.account_head === tax.account_head);

                                // console.log(existingRowIndex)
                                // console.log(frm.doc.taxes)
                                // frm.doc.taxes.splice(existingRowIndex, 1);
                                // frm.refresh_field("taxes");
                                // console.log(frm.doc.taxes)
                                // frm.add_child("taxes", tax);
                                var newValues  = { rate: tax.rate, tax_amount: tax.tax_amount, tax_amount_after_discount_amount:tax.tax_amount_after_discount_amount,
                                    base_tax_amount: tax.base_tax_amount, base_tax_amount_after_discount_amount: tax.base_tax_amount_after_discount_amount}
                                Object.assign(frm.doc.taxes[existingRowIndex], newValues);
                            }
                        });
                    } else {
                        frm.set_value("taxes", r.message);
                    }
                }

            }
        })


    },
    cnp_expected_installation_date: frm => {
        update_due_date(frm)
    },
    cnp_installation_date: frm => {
        update_due_date(frm)
    },
    taxes_and_charges: frm => {

    },
    taxes_and_charges_overide: frm => {
            return frm.call({
              method: "minix.minix.overrides.purchase_invoice.get_taxes_and_charges_override",
              args: {
                "master_doctype": frappe.meta.get_docfield(frm.doc.doctype, "taxes_and_charges", frm.doc.name).options,
                "master_name": frm.doc.taxes_and_charges,
                "supplier": frm.doc.supplier,
                "posting_date": frm.doc.posting_date,
                "company": frm.doc.company,
                "taxes_and_charges_overide":frm.doc.taxes_and_charges_overide
              },
              callback: function(r) {
                if (!r.exc) {
                  if (frm.doc.shipping_rule && frm.doc.taxes) {
                    for (let tax of r.message) {
                      frm.add_child("taxes", tax);
                    }
                    refresh_field("taxes");
                  } else {
                    frm.set_value("taxes", r.message);
                  }
                }
              }
            });
        //   }

    },
  

})
function set_read_only(frm) {
    frm.fields_dict.taxes.grid.update_docfield_property(
        'tax_amount',
        'read_only',
        !frm.doc.cnp_is_debit_note,
    );
    frm.fields_dict.taxes.grid.update_docfield_property(
        'total',
        'read_only',
        !frm.doc.cnp_is_debit_note,
    );
}

function update_due_date(frm) {
    let installation_date = frm.doc.cnp_installation_date
    let expected_installation_date = frm.doc.cnp_expected_installation_date
    if (frm.doc.cnp_is_installed && installation_date) {
        frm.doc.payment_schedule[0].due_date = installation_date;
        frm.doc.due_date = installation_date;
    }
    else if (!frm.doc.cnp_is_installed && expected_installation_date) {
        frm.doc.payment_schedule[0].due_date = expected_installation_date;
        frm.doc.due_date = expected_installation_date;
    }
}
erpnext.taxes.set_conditional_mandatory_rate_or_amount = function (grid_row) {
    if (grid_row) {
        if (grid_row.doc.charge_type === "Actual") {
            grid_row.toggle_editable("tax_amount", true);
            grid_row.toggle_reqd("tax_amount", true);
            grid_row.toggle_editable("rate", true);
            grid_row.toggle_reqd("rate", false);
        } else {
            grid_row.toggle_editable("rate", true);
            grid_row.toggle_reqd("rate", true);
            grid_row.toggle_editable("tax_amount", false);
            grid_row.toggle_reqd("tax_amount", false);
        }
    }
}

erpnext.taxes_and_totals.prototype.set_cumulative_total = function (row_idx, tax) {
    if (tax.add_deduct_tax == "Deduct" && this.frm.doc.apply_tds && this.frm.doc.cnp_multi_tsd && this.frm.doc.taxes_and_charges_overide) {
        tax.total = this.frm.doc.items[row_idx].base_amount
    }
    else {
        var tax_amount = tax.tax_amount_after_discount_amount;
        if (tax.category == 'Valuation') {
            tax_amount = 0;
        }
        if (tax.add_deduct_tax == "Deduct") { tax_amount = -1 * tax_amount; }
        if (row_idx == 0) {
            tax.total = flt(this.frm.doc.net_total + tax_amount, precision("total", tax));
        } else {
            tax.total = flt(this.frm.doc["taxes"][row_idx - 1].total + tax_amount, precision("total", tax));
        }
    }
}