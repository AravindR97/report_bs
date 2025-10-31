frappe.listview_settings["Sales Invoice"] = {
    button: {
        show: function (doc) {
            return doc.docstatus === 1;
        },
        get_label: function (doc) {
            let icon_color = "gray";
            let icon_title = "Make Payment"

            if (doc.outstanding_amount == 0) {
                icon_color = "green"; // fully paid
                icon_title = "Full Paid";
            } else if (doc.outstanding_amount < doc.grand_total) {
                icon_color = "orange"; // partially paid
                icon_title = "Partially Paid";
            } else {
                icon_color = "red"; // not paid
                icon_title = "Unpaid";
            }

            // placeholder for drafts — will be filled async
            let draft_badge = `<span class="payment-draft-count" 
                                    data-name="${doc.name}"
                                    style="background:#dce0e3; color:#555; border-radius:50%; 
                                           padding:2px 6px; font-size:11px; margin-right:6px;">
                                    ...
                               </span>`;

            let payment_icon = `<i class="fa fa-credit-card" 
                                    style="font-size:14px; color:${icon_color};">
                                 </i>`;

            // trigger async API to load counts
            frappe.call({
                method: "report_bs.api.get_payment_entry_info",
                args: { invoice_name: doc.name },
                callback: function (r) {
                    if (r.message && $(".payment-draft-count[data-name='" + doc.name + "']").length) {
                        const drafts = r.message.drafts || 0;
                        const el = $(".payment-draft-count[data-name='" + doc.name + "']");
                        if (drafts > 0) {
                            el.text(drafts);
                            el.css({
                                background: "#c4c3c0ff",
                                color: "#000",
                                fontWeight: "bold",
                            });
                            el.attr("title", `${drafts} draft payment entr${drafts > 1 ? "ies" : "y"} exist`);
                        } else {
                            el.remove(); // hide badge if no drafts
                        }
                    }
                }
            });

            return draft_badge + payment_icon;
        },
        get_description: function (doc) {
            let icon_title = "Make Payment"
            if (doc.outstanding_amount == 0) {
                icon_title = "Full Paid";
            } else if (doc.outstanding_amount < doc.grand_total) {
                icon_title = "Partially Paid";
            } else {
                icon_title = "Unpaid";
            }
            return __(icon_title);
        },
        action: function (doc) {
            if (doc.outstanding_amount == 0) {
                frappe.msgprint("This invoice is fully paid");
            } else {
                frappe.db.get_doc("Sales Invoice", doc.name).then(full_doc => {
                    const d = new frappe.ui.Dialog({
                        title: __("Create Payment Entry"),
                        fields: [
                            {
                                fieldname: "paid_amount",
                                label: "Payment Amount",
                                fieldtype: "Currency",
                                reqd: 1,
                                default: full_doc.outstanding_amount
                            },
                            {
                                fieldname: "mode_of_payment",
                                label: "Mode of Payment",
                                fieldtype: "Link",
                                options: "Mode of Payment",
                                reqd: 1,
                                onchange: function () {
                                    let mode = d.get_value("mode_of_payment");

                                    if (mode && mode !== "Cash") {
                                        d.set_df_property("ref_no", "reqd", 1);
                                        d.set_df_property("ref_date", "reqd", 1);
                                        d.set_df_property("ref_no", "hidden", 0);
                                        d.set_df_property("ref_date", "hidden", 0);
                                    } else {
                                        d.set_df_property("ref_no", "reqd", 0);
                                        d.set_df_property("ref_date", "reqd", 0);
                                        d.set_df_property("ref_no", "hidden", 1);
                                        d.set_df_property("ref_date", "hidden", 1);
                                    }
                                }
                            },
                            {
                                fieldname: "ref_no",
                                label: "Reference No",
                                fieldtype: "Data",
                                hidden: 1
                            },
                            {
                                fieldname: "ref_date",
                                label: "Reference Date",
                                fieldtype: "Date",
                                hidden: 1
                            },
                        ],
                        primary_action_label: __("Create"),
                        primary_action(values) {
                            frappe.call({
                                method: "report_bs.api.create_payment_entry",
                                args: {
                                    sales_invoice: full_doc.name,
                                    company: full_doc.company,
                                    customer: full_doc.customer,
                                    currency: full_doc.currency,
                                    outstanding_amount: full_doc.outstanding_amount,
                                    paid_amount: values.paid_amount,
                                    mode_of_payment: values.mode_of_payment,
                                    ref_no: values.ref_no,
                                    ref_date: values.ref_date
                                },
                                callback: function (r) {
                                    if (!r.exc) {
                                        frappe.show_alert({
                                            message: __("Draft Payment Entry {0} created", [r.message.name]),
                                            indicator: "green"
                                        });
                                        d.hide();
                                        if (frappe.listview && frappe.listview.list_view) {
                                            frappe.listview.list_view.refresh();
                                        } else if (cur_list) {
                                            cur_list.refresh();
                                        }
                                    }
                                }
                            });
                        }
                    });
                    d.show();
                });
            }
        }
    },
    onload(listview) {
        // Hide the sidebar
        const sidebar = document.querySelector('.layout-side-section');
        if (sidebar) {
            sidebar.style.display = 'none';
        }

        // Expand main section to full width
        const main_section = document.querySelector('.layout-main-section-wrapper');
        if (main_section) {
            main_section.style.flex = '1';
        }
    }
};
