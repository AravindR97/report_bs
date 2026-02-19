import frappe

def after_insert(doc, method=None):
    if doc.docstatus != 0:
        return

    references = [
        d.reference_name
        for d in doc.references
        if d.reference_doctype == "Sales Invoice"
    ]

    if len(references) == 1:
        frappe.publish_realtime(
            "payment_entry_draft_created",
            {
                "sales_invoice": references[0]
            }
        )
