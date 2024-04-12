import frappe
from frappe.utils import now_datetime, add_days, formatdate, getdate

@frappe.whitelist()
def get_due_date_based_on_condition(pr):
    purchase_receipt = frappe.get_doc("Purchase Receipt", pr)
    purchase_order = frappe.get_doc("Purchase Order", purchase_receipt.items[0].purchase_order)

    payment_term = None
    if purchase_order.payment_schedule:
        payment_term = purchase_order.payment_schedule[0].payment_term

    if payment_term:
        due_date_based_on = frappe.get_value("Payment Term", payment_term, "due_date_based_on")
        days_to_add = frappe.get_value("Payment Term", payment_term, "credit_days")

        if due_date_based_on == "After invoice creation":
            today_datetime = now_datetime()
            new_date = add_days(today_datetime, days_to_add)
            return {"due_date":frappe.utils.formatdate(new_date.date(), "yyyy-mm-dd")}
        elif due_date_based_on == "After PR is created":
            today_datetime = purchase_receipt.posting_date
        else:
            # Handle the case when due_date_based_on is not in either dictionary
            if due_date_based_on in ["Completion of Work","On Installation"]:
                return {"status":True}
            return None

        new_date = add_days(today_datetime, days_to_add)
        return {"due_date":new_date}

    # Handle the case when payment_term is not found
    return None


@frappe.whitelist()
def get_tax_withholding_details(tax_withholding_category, posting_date, company):
    tax_withholding = frappe.get_doc("Tax Withholding Category", tax_withholding_category)

    tax_rate_detail = get_tax_withholding_rates(tax_withholding, posting_date)

    for account_detail in tax_withholding.accounts:
        if company == account_detail.company:
            return frappe._dict(
                {
                    "tax_withholding_category": tax_withholding_category,
                    "account_head": account_detail.account,
                    "rate": tax_rate_detail.tax_withholding_rate,
                    "from_date": tax_rate_detail.from_date,
                    "to_date": tax_rate_detail.to_date,
                    "threshold": tax_rate_detail.single_threshold,
                    "cumulative_threshold": tax_rate_detail.cumulative_threshold,
                    "description": tax_withholding.category_name
                    if tax_withholding.category_name
                    else tax_withholding_category,
                    "consider_party_ledger_amount": tax_withholding.consider_party_ledger_amount,
                    "tax_on_excess_amount": tax_withholding.tax_on_excess_amount,
                    "round_off_tax_amount": tax_withholding.round_off_tax_amount,
                }
            )

def get_tax_withholding_rates(tax_withholding, posting_date):
    # returns the row that matches with the fiscal year from posting date
    for rate in tax_withholding.rates:
        if getdate(rate.from_date) <= getdate(posting_date) <= getdate(rate.to_date):
            return rate

    frappe.throw("No Tax Withholding data found for the current posting date.")



@frappe.whitelist()
def get_is_car_hired(name):
    account_heads = ''
    doc = frappe.get_doc("Purchase Taxes and Charges Template", name)	
    if doc.taxes:
        account_heads = doc.taxes

    return {"account_heads":account_heads, "is_car_hired":doc.is_car_hired}