# Copyright (c) 2025, aravind@enfono.com and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    if not filters:
        filters = {}

    # Ensure all required filters are set
    required = ["customer", "from_date", "to_date"]
    for f in required:
        if not filters.get(f):
            frappe.throw(f"Please set {f.replace('_', ' ').title()} before running the report.")

    # Add required data in filters
    customer = filters.get('customer')
    meta = frappe.get_meta("Customer")
    if meta.has_field("custom_vat_registration_number"):
        customer_vat_no = frappe.db.get_value("Customer", customer, "custom_vat_registration_number")
        filters['customer_vat_no'] = customer_vat_no or None

    user = frappe.session.user
    employee = frappe.db.get_value("Employee", {"user_id": user}, "employee_name")
    filters['created_by'] = employee or user


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
    # Fetch opening balance before from_date
    opening_balance = get_opening_balance(filters)

    conditions = [
        "party_type = 'Customer'",
        "party = %(customer)s",
        "posting_date >= %(from_date)s",
        "posting_date <= %(to_date)s"
    ]

    values = {
        "customer": filters["customer"],
        "from_date": filters["from_date"],
        "to_date": filters["to_date"],
    }

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
            {" AND ".join(conditions)}
        ORDER BY posting_date, creation
    """, values, as_dict=True)

    data = []

    # Add opening balance row
    data.append({
        "posting_date": None,
        "voucher_type": "Opening Balance",
        "voucher_no": "",
        "against_voucher": "",
        "debit": 0,
        "credit": 0,
        "balance": opening_balance
    })

    balance = opening_balance

    for d in gl_entries:
        balance += d.debit - d.credit
        if d.voucher_type == d.against_voucher_type:
            d.against_voucher = None
        d.balance = balance
        data.append(d)

    # Add closing balance row
    data.append({
        "posting_date": None,
        "voucher_type": "Closing Balance",
        "voucher_no": "",
        "against_voucher": "",
        "debit": 0,
        "credit": 0,
        "balance": data[len(data) - 1].balance
    })

    # add required data as last row of the table
    data.append({
        "customer_vat_no": filters['customer_vat_no'],
        "created_by": filters['created_by']
    })

    
    return data


def get_opening_balance(filters):
    """Compute opening balance before from_date."""
    result = frappe.db.sql("""
        SELECT
            SUM(debit) - SUM(credit) AS balance
        FROM
            `tabGL Entry`
        WHERE
            party_type = 'Customer'
            AND party = %(customer)s
            AND posting_date < %(from_date)s
    """, {"customer": filters["customer"], "from_date": filters["from_date"]}, as_dict=True)

    return result[0].balance or 0
