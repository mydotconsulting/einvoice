frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        if(frm.doc.docstatus == 1){ 
            frappe.call({
                method:"frappe.client.get",
                args:{
                    doctype:"Customer",
                    name : frm.doc.customer
                },
                fields:["custom_tin"],
                callback:function(r){
                    if(r.message && r.message.custom_tin){

                        if (frm.doc.custom_invoice_status == "Pending") {
                            frm.add_custom_button('Post Invoice', function() {
                                frappe.confirm(
                                    'Are you sure you want to upload this invoice?',
                                    function() {
                                        frappe.call({
                                            method: "malaysiainvoice.custom.generateinvoice.post_sales_invoice",
                                            args: {
                                                doc:frm.doc.name
                                            },
                                            callback: function(r) {
                                                if (r.message) {
                                                    console.log("Message : ",r.message)
                                                    // frappe.msgprint(r.message);
                                                }
                                            }
                                        });
                                    }
                                );
                            },__("MyInvoice"));
                        }
                        if (frm.doc.custom_invoice_status == "Uploaded" && frm.doc.custom_document_uid) {
                            frm.add_custom_button('Cancel Invoice', function() {
                                frappe.prompt(
                                    [
                                        {
                                            label: 'Reason for Cancellation',
                                            fieldname: 'cancellation_reason',
                                            fieldtype: 'Small Text',
                                            reqd: 1
                                        }
                                    ],
                                    function(values) {
                                        frappe.call({
                                            method: "malaysiainvoice.custom.generateinvoice.cancel_invoice",
                                            args: {
                                                invoice_id: frm.doc.name,
                                                reason: values.cancellation_reason
                                            },
                                            callback: function(r) {
                                                if (r.message) {
                                                    console.log("Response : ", r.message)
                                                    // frappe.msgprint(r.message);
                                                }
                                            }
                                        });
                                    },
                                    'Cancel Invoice',
                                    'Submit'
                                );
                            }, __("MyInvoice"));
                        }
                    }
                }
            })            
        }
    }
});
