import frappe



def before_save(doc,method):
    if doc.cnp_tds_details:
        doc.cnp_multi_tsd = 1
    else:
        doc.cnp_multi_tsd = 0