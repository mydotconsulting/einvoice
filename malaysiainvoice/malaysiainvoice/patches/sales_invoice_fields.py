
import frappe

def execute():
    custom_fields = [
        {
            "doctype": "Custom Field",
            "dt": "Sales Invoice",
            "fieldname": "custom_tax_setcion_details",
            "fieldtype": "Section Break",
            "label": "LHDN Details",
            "insert_after": "amended_from",
            "collapsible" : 1
        },
        {
            "doctype": "Custom Field",
            "dt": "Sales Invoice",
            "fieldname": "custom_supplier",
            "fieldtype": "Link",
            "label": "Supplier",
            "options": "Supplier",
            "insert_after": "custom_tax_setcion_details"
        },
        {
            "doctype": "Custom Field",
            "dt": "Sales invoice",
            "fieldname": "custom_col_01",
            "fieldtype": "Column Break",
            "insert_after": "custom_supplier"
        },
        {
            "doctype": "Custom Field",
            "dt": "Sales Invoice",
            "fieldname": "custom_invoice_status",
            "fieldtype": "Select",
            "label": "Invoice Status",
            "options": "\nPending\nUploaded\nCancelled",
            "insert_after": "custom_col_01",
            "allow_on_submit":1,
            "read_only":1,
            "default":"Pending"
        },
        {
            "doctype": "Custom Field",
            "dt": "Sales invoice",
            "fieldname": "custom_col_02",
            "fieldtype": "Column Break",
            "insert_after": "custom_invoice_status"
        },
        {
            "doctype": "Custom Field",
            "dt": "Sales Invoice",
            "fieldname": "custom_document_uid",
            "fieldtype": "Data",
            "label": "Document UID",
            "insert_after": "custom_col_02",
            "allow_on_submit":1,
            "read_only":1
        }
    ]

    for field in custom_fields:
        try:
            if not frappe.db.exists("Custom Field", {"dt": field["dt"], "fieldname": field["fieldname"]}):
                frappe.get_doc(field).insert()
                frappe.db.commit()  # Commit after each successful insertion
        except Exception as e:
            frappe.log_error(f"Failed to create custom field {field['fieldname']}: {str(e)}")
