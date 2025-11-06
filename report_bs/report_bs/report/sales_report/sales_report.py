# Copyright (c) 2025, aravind@enfono.com and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    # -------------------------------
    # Define Columns
    # -------------------------------
    columns = [
        {"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": "Invoice No", "fieldname": "invoice_no", "fieldtype": "Link", "options": "Sales Invoice", "width": 200},
        {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 150},
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
        {"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 200},
        {"label": "Items", "fieldname": "items", "fieldtype": "Text", "width": 300},
        {"label": "Total", "fieldname": "total", "fieldtype": "Currency", "width": 100},
        {"label": "Tax", "fieldname": "tax", "fieldtype": "Currency", "width": 100},
        {"label": "Discount", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 100},
        {"label": "Grand Total", "fieldname": "grand_total", "fieldtype": "Currency", "width": 120},
        {"label": "Paid", "fieldname": "paid", "fieldtype": "Currency", "width": 100},
        {"label": "Balance", "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 100},
        {"label": "Created By", "fieldname": "created_by", "fieldtype": "Data", "width": 180},
    ]

    # -------------------------------
    # Build Conditions
    # -------------------------------
    conditions = ["si.docstatus = 1"]  # Only submitted invoices

    if filters.get("from_date") and filters.get("to_date"):
        conditions.append("si.posting_date BETWEEN %(from_date)s AND %(to_date)s")
    else:
        frappe.throw("Please select both From Date and To Date")

    if filters.get("customer"):
        conditions.append("si.customer = %(customer)s")

    if filters.get("created_by"):
        conditions.append("si.owner = %(created_by)s")

    if filters.get("item"):
        conditions.append("""si.name IN (
            SELECT parent FROM `tabSales Invoice Item` WHERE item_code = %(item)s
        )""")

    condition_str = " AND ".join(conditions)

    # -------------------------------
    # Main Query
    # -------------------------------
    invoices = frappe.db.sql(f"""
        SELECT
            si.name AS invoice_no,
            si.posting_date,
            si.set_warehouse AS warehouse,
            si.customer,
            si.customer_name,
            si.total,
            si.discount_amount,
            si.grand_total,
            si.outstanding_amount,
            si.owner
        FROM `tabSales Invoice` si
        WHERE {condition_str}
        ORDER BY si.posting_date DESC
    """, filters, as_dict=True)

    data = []

    for inv in invoices:
        # -------------------------------
        # Get Item details
        # -------------------------------
        items = frappe.db.sql("""
            SELECT item_name, uom, qty
            FROM `tabSales Invoice Item`
            WHERE parent = %s
        """, inv.invoice_no, as_dict=True)

        item_lines = []
        for it in items:
            item_lines.append(f"{it.item_name} ({it.uom} - {it.qty})")

        items_text = ", ".join(item_lines)

        # -------------------------------
        # Get Total Tax from Taxes Table
        # -------------------------------
        tax_amount = frappe.db.sql("""
            SELECT SUM(tax_amount)
            FROM `tabSales Taxes and Charges`
            WHERE parent = %s
        """, inv.invoice_no)[0][0] or 0

        # -------------------------------
        # Calculate Paid Amount
        # -------------------------------
        paid = (inv.grand_total or 0) - (inv.outstanding_amount or 0)

        # -------------------------------
        # Get Creator Full Name via Employee
        # -------------------------------
        created_by_name = frappe.db.get_value(
            "Employee",
            {"user_id": inv.owner},
            "employee_name"
        ) or frappe.db.get_value("User", inv.owner, "full_name")

        # -------------------------------
        # Append Row
        # -------------------------------
        data.append({
            "posting_date": inv.posting_date,
            "invoice_no": inv.invoice_no,
            "warehouse": inv.warehouse,
            "customer": inv.customer,
            "customer_name": inv.customer_name,
            "items": items_text,
            "total": inv.total,
            "tax": tax_amount,
            "discount_amount": inv.discount_amount,
            "grand_total": inv.grand_total,
            "paid": paid,
            "outstanding_amount": inv.outstanding_amount,
            "created_by": created_by_name,
        })

    return columns, data

