// Copyright (c) 2025, aravind@enfono.com and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Report"] = {
    "filters": [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.get_today()
        },
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer"
        },
        {
            fieldname: "item",
            label: __("Item"),
            fieldtype: "Link",
            options: "Item"
        },
        {
            fieldname: "created_by",
            label: __("Created By"),
            fieldtype: "Link",
            options: "User"
        }
    ],

	onload: function(report) {
        const style = document.createElement("style");
        style.innerHTML = `
            .report-view .dt-cell__content[data-fieldname="items"] {
                white-space: normal !important;
                word-break: break-word !important;
                overflow-wrap: anywhere !important;
            }
        `;
        document.head.appendChild(style);
    }
};
