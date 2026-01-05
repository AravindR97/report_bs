# Copyright (c) 2025, aravind@enfono.com and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    if not filters:
        filters = {}

    required = ["customer", "from_date", "to_date"]
    for f in required:
        if not filters.get(f):
            frappe.msgprint("Please set all filters before running the report.", alert=True)
            return

    customer = filters.get("customer")
    meta = frappe.get_meta("Customer")
    if meta.has_field("custom_vat_registration_number"):
        filters["customer_vat_no"] = frappe.db.get_value(
            "Customer", customer, "custom_vat_registration_number"
        )

    user = frappe.session.user
    employee = frappe.db.get_value("Employee", {"user_id": user}, "employee_name")
    filters["created_by"] = employee or user

    return get_columns(), get_data(filters)


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
    opening_balance = get_opening_balance(filters)

    gl_entries = frappe.db.sql(
        """
        SELECT
            posting_date,
            voucher_type,
            voucher_subtype,
            voucher_no,
            against_voucher_type,
            against_voucher,
            debit,
            credit
        FROM `tabGL Entry`
        WHERE
            party_type = 'Customer'
            AND party = %(customer)s
            AND posting_date BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY posting_date, creation
        """,
        filters,
        as_dict=True,
    )

    data = []

    data.append({
        "posting_date": None,
        "voucher_type": "Opening Balance",
        "voucher_subtype": "",
        "voucher_no": "",
        "against_voucher": "",
        "debit": 0,
        "credit": 0,
        "balance": opening_balance,
    })

    balance = opening_balance
    credit_sum = debit_sum = credit_notes = 0

    for d in gl_entries:
        debit = d.get("debit", 0)
        credit = d.get("credit", 0)

        balance += debit - credit
        debit_sum += debit

        if d.get("voucher_subtype") == d.get("against_voucher_type"):
            d["against_voucher"] = None

        if d.get("voucher_subtype") == "Credit Note":
            d["voucher_type"] = "Credit Note"
            credit_notes += credit

        if d.get("voucher_type") == "Payment Entry":
            credit_sum += credit

        d["balance"] = balance
        data.append(d)

    data.append({
        "posting_date": None,
        "voucher_type": "Closing Balance",
        "voucher_subtype": "",
        "voucher_no": "",
        "against_voucher": "",
        "debit": None,
        "credit": None,
        "balance": balance,
    })

    data.append({
        "customer_vat_no": filters.get("customer_vat_no"),
        "created_by": filters["created_by"],
        "statement_date": frappe.utils.today(),
        "credit_sum": credit_sum,
        "debit_sum": debit_sum,
        "credit_notes": credit_notes,
        "debit": None,
        "credit": None,
        "balance": None,
    })

    return data


def get_opening_balance(filters):
    result = frappe.db.sql(
        """
        SELECT
            COALESCE(SUM(debit), 0) - COALESCE(SUM(credit), 0) AS balance
        FROM `tabGL Entry`
        WHERE
            party_type = 'Customer'
            AND party = %(customer)s
            AND posting_date < %(from_date)s
        """,
        filters,
        as_dict=True,
    )

    return result[0]["balance"] if result else 0
