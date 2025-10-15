# Copyright (c) 2025, aravind@enfono.com and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": "Voucher Type", "fieldname": "voucher_type", "fieldtype": "Data", "width": 150},
        {"label": "Voucher No", "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 180},
        {"label": "Against Voucher", "fieldname": "against_voucher", "fieldtype": "Dynamic Link", "options": "against_voucher_type", "width": 180},
        {"label": "Debit", "fieldname": "debit", "fieldtype": "Currency", "width": 120},
        {"label": "Credit", "fieldname": "credit", "fieldtype": "Currency", "width": 120},
        {"label": "Balance", "fieldname": "balance", "fieldtype": "Currency", "width": 120},
    ]

def get_data(filters):
    conditions = []
    values = {}

    if filters.get("customer"):
        conditions.append("party_type = 'Customer' AND party = %(customer)s")
        values["customer"] = filters["customer"]

    if filters.get("from_date"):
        conditions.append("posting_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("posting_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    gl_entries = frappe.db.sql(f"""
        SELECT
            posting_date,
            voucher_type,
            voucher_no,
            against_voucher_type,
            against_voucher,
            debit,
            credit
        FROM
            `tabGL Entry`
        WHERE
            {where_clause}
        ORDER BY posting_date, creation
    """, values, as_dict=True)

    data = []
    balance = 0

    for d in gl_entries:
        balance += d.debit - d.credit
        # Custom condition
        if d.voucher_type == d.against_voucher_type:
            d.against_voucher = None
        d.balance = balance
        data.append(d)

    return data
