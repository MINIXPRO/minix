# Copyright (c) 2024, Meril and contributors
# For license information, please see license.txt

# import frappe


from minix.minix.overrides.accounts_receivable import ReceivablePayableReport


def execute(filters=None):
	args = {
		"account_type": "Payable",
		"naming_by": ["Buying Settings", "supp_master_name"],
	}
	return ReceivablePayableReport(filters).run(args)
