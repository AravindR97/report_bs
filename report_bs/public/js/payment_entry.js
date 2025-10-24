frappe.ui.form.on("Payment Entry", {
    custom_round_off_unallocated_amount: function(frm){
        if(frm.doc.unallocated_amount > 0){
            frm.clear_table("deductions");
            let company = frappe.defaults.get_global_default("company");
            if(!company){
                frappe.msgprint("Default company not set in Gobal Defaults");
                return
            } else {
                frappe.db.get_value("Company", company, ["round_off_account", "round_off_cost_center"])
                .then(r=>{
                    if(r && r.message){
                        if(!r.message.round_off_account || !r.message.round_off_cost_center ){
                           frappe.msgprint(`Default Round Off account or cost center not set for company: ${company}`);
                           return
                        } else {
                            const row = frm.add_child("deductions");
                            
                            frappe.model.set_value(row.doctype, row.name, "account", r.message.round_off_account);
                            frappe.model.set_value(row.doctype, row.name, "cost_center", r.message.round_off_cost_center);
                            frappe.model.set_value(row.doctype, row.name, "amount", frm.doc.unallocated_amount * -1);

                            frm.refresh_field("deductions")
                        }
                    }
                });
            }
        }
    }
});