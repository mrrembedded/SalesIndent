// Copyright (c) 2024, MRR and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Invoice Indent', {
	refresh: function(frm) {
        // Set filters for billing_from and shipment_from fields
        frm.fields_dict['billing_from'].get_query = function() {
            return {
                filters: [
                    ['Address', 'address_type', '=', 'Shipping']
                ]
            };
        };
        frm.fields_dict['shipment_from'].get_query = function() {
            return {
                filters: [
                    ['Address', 'address_type', '=', 'Shipping']
                ]
            };
        };

    }

    // before_save: function(frm) {
    //     var value = frm.doc.vehicle_no;
    //     // Validate vehicle number format using regex
    //     var regex = /^[A-Z]{2}[ -]?[0-9]{2}[ -]?[A-Z]{1,2}[ -]?[0-9]{4}$/;
    //     frappe.msgprint("before");
    //     if (!regex.test(value)) {
    //         frappe.msgprint("before sav");
    //         // Raise a validation error if format is invalid
    //          throw new frappe.ValidationError("Vehicle number should be in correct format");
    //     }
    // },


    // on_submit: function(frm) {
        
    //     frappe.call({
            
    //         method: 'erpnext.sppbilling.doctype.test_sample.test_sample.create_sales_invoice',
    //         callback: function(r) {
    //             if (r.message) {
                    
    //             }
    //         }
    //     });
    // }
});
