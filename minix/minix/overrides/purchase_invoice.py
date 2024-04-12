from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
import frappe
from erpnext.accounts.doctype.tax_withholding_category.tax_withholding_category import (
	get_party_tax_withholding_details,
)
from minix.minix.methods.purchase_invoice import get_tax_withholding_details

class CustomPurchaseInvoice(PurchaseInvoice):
    def validate(self):
        taxes = self.get("taxes")
        tax_dict = {tax.name: tax.rate for tax in taxes if tax.charge_type == 'Actual'}
        tax_totals = {tax.name: tax.total for tax in taxes if tax.charge_type == 'Actual'}
        super(CustomPurchaseInvoice, self).validate()
        for tax in self.taxes:
            if tax.charge_type == 'Actual':
                if tax.name:
                    tax.rate = tax_dict[tax.name]
                    tax.total = tax_totals[tax.name]
    
    def set_tax_withholding(self):
        if not self.apply_tds:
            return

        if self.apply_tds and not self.get("tax_withholding_category"):
            self.tax_withholding_category = frappe.db.get_value(
                "Supplier", self.supplier, "tax_withholding_category"
            )
        supplie_tds = frappe.get_doc("Supplier",self.supplier)

        # if supplie_tds.cnp_tds_details:
        #     return
        if self.taxes_and_charges_overide:
            return
        
        if not self.tax_withholding_category :
            return

        tax_withholding_details, advance_taxes, voucher_wise_amount = get_party_tax_withholding_details(
            self, self.tax_withholding_category
        )
        # Adjust TDS paid on advances
        self.allocate_advance_tds(tax_withholding_details, advance_taxes)

        if not tax_withholding_details:
            return

        accounts = []
        for d in self.taxes:
            if d.account_head == tax_withholding_details.get("account_head"):
                d.update(tax_withholding_details)

            accounts.append(d.account_head)

        if not accounts or tax_withholding_details.get("account_head") not in accounts:
            self.append("taxes", tax_withholding_details)

        to_remove = [
            d
            for d in self.taxes
            if not d.tax_amount and d.account_head == tax_withholding_details.get("account_head")
        ]

        for d in to_remove:
            self.remove(d)
        
        ## Add pending vouchers on which tax was withheld
        self.set("tax_withheld_vouchers", [])

        for voucher_no, voucher_details in voucher_wise_amount.items():
            self.append(
                "tax_withheld_vouchers",
                {
                    "voucher_name": voucher_no,
                    "voucher_type": voucher_details.get("voucher_type"),
                    "taxable_amount": voucher_details.get("amount"),
                },
            )

        # calculate totals again after applying TDS
        self.calculate_taxes_and_totals()


@frappe.whitelist()
def get_supplier_tds_details(supplier,posting_date,company):
    records = []
    supplier_tds = frappe.get_doc("Supplier", supplier)
    if not supplier_tds.cnp_tds_details and not supplier_tds.tax_withholding_category:
        return None
    
    for tax in supplier_tds.cnp_tds_details:
        tax_withholding_cat = frappe.get_doc("Tax Withholding Category", tax.tax_withholding_category)
        rate = get_tax_withholding_details(tax.tax_withholding_category, posting_date, company).get("rate")
        if tax_withholding_cat.accounts:
            for account in tax_withholding_cat.accounts:
                data = {}
                data["charge_type"] = tax.tax_withholding_category
                data["account_head"] = account.account
                data['rate'] = rate
                records.append(data)
    return records

def get_tax_json(tax):
    return {
            'category': 'Total',
            'add_deduct_tax': 'Deduct', 
            'charge_type': 'Actual', 
            'row_id': None, 
            'included_in_print_rate': 0, 
            'included_in_paid_amount': 0, 
            'account_head': tax.get("account_head"), 
            'description': tax.get("charge_type"), 
            'rate': tax.get("rate"), 
            'base_amount': 0.0, 
            'cost_center': 'Main - MCPL', 
            'segment': None, 
            'account_currency': 'INR', 
            'tax_amount': tax.get("tax_amount", 0.0), 
            'tax_amount_after_discount_amount': 0.0, 
            'total': 0.0, 
            'base_tax_amount': 0.0, 
            'base_total': 0.0, 
            'base_tax_amount_after_discount_amount': 0.0, 
            'item_wise_tax_detail': None
        }


@frappe.whitelist()
def get_taxes_and_charges_override(master_doctype, master_name,supplier,posting_date,company,taxes_and_charges_overide):
    if not master_name:
        return
    from frappe.model import child_table_fields, default_fields

    tax_master = frappe.get_doc(master_doctype, master_name)

    taxes_and_charges = []
    for i, tax in enumerate(tax_master.get("taxes")):
        tax = tax.as_dict()
        for fieldname in default_fields + child_table_fields:
            if fieldname in tax:
                del tax[fieldname]

        taxes_and_charges.append(tax)
    if taxes_and_charges_overide !="0":
        sup_tax = get_supplier_tds_details(supplier,posting_date,company)
        for tax in sup_tax:
            taxes_and_charges.append(get_tax_json(tax))
    return taxes_and_charges


@frappe.whitelist()
def get_item_wise_tax_rcm(taxes_and_charges, items):
    import json
    items = json.loads(items)
    from minix.minix.methods.purchase_invoice import get_is_car_hired
    accounts = []
    tax_accounts = get_is_car_hired(taxes_and_charges)['account_heads']
    # if not get_is_car_hired(taxes_and_charges)['is_car_hired']:
    #     return
    for acc in tax_accounts:
        accounts.append(acc.account_head)
    taxes = []
    for item in items:
        if item.get('payable_but_not_receivable_rcm') and item.get('item_tax_template'):
            tax_rate = get_item_wise_tax(item, accounts)
            total = (item['amount'] / 100) * tax_rate
            tax_dict = {
                'category': 'Total',
                'add_deduct_tax': 'Add', 
                'charge_type': 'Actual', 
                'row_id': None, 
                'included_in_print_rate': 0, 
                'included_in_paid_amount': 0, 
                'account_head': item['expense_account'], 
                'description': "Return Car hire", 
                'rate': tax_rate, 
                'base_amount': 0.0, 
                'cost_center': 'Main - MCPL', 
                'segment': None, 
                'account_currency': 'INR', 
                'tax_amount': total, 
                'tax_amount_after_discount_amount': total, 
                'total': 0.0, 
                'base_tax_amount':total, 
                'base_total': 0.0, 
                'base_tax_amount_after_discount_amount': total, 
                'item_wise_tax_detail': None
            }
            taxes.append(tax_dict)
    result = {}
    for item in taxes:  # Iterating over 'taxes' list, not 'tax_dict' dictionary
        account_head = item.get('account_head')  # Accessing dictionary keys using get() method
        tax_amount = item.get('tax_amount', 0)   # Accessing dictionary keys using get() method with default value 0
        if account_head in result:
            result[account_head]['tax_amount'] += tax_amount
        else:
            result[account_head] = item

    # Convert result dictionary back to a list
    final_result = list(result.values())
    return final_result

    
def get_item_wise_tax(item,accounts):
    tax_rate = 0
    gst_doc = frappe.get_doc("Item Tax Template", item.get('item_tax_template'))
    for gst_account in gst_doc.taxes:
        if gst_account.tax_type in accounts:
            tax_rate += gst_account.tax_rate
    return tax_rate


@frappe.whitelist()
def get_tax_holding_details(self):
    if self.apply_tds and not self.get("tax_withholding_category"):
        self.tax_withholding_category = frappe.db.get_value(
            "Supplier", self.supplier, "tax_withholding_category"
        )
    supplie_tds = frappe.get_doc("Supplier",self.supplier)

    # if supplie_tds.cnp_tds_details:
    #     return
    if self.taxes_and_charges_overide:
        return
    
    if not self.tax_withholding_category :
        return

    tax_withholding_details, advance_taxes, voucher_wise_amount = get_party_tax_withholding_details(
        self, self.tax_withholding_category
    )
    return tax_withholding_details



@frappe.whitelist()
def check_suplier_multiple_tds(supplier):
    return frappe.get_value("Supplier", supplier, "cnp_multi_tsd")