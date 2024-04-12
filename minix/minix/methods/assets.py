import frappe


@frappe.whitelist()
def schedule_asset_depreciation():
    frappe.enqueue('erpnext.assets.doctype.asset.asset.make_post_gl_entry')