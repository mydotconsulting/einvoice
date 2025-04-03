import frappe

def execute():
    custom_fields = [
        {
            "doctype": "Custom Field",
            "dt": "Company",
            "fieldname": "custom_portal_credentials",
            "fieldtype": "Section Break",
            "label": "Portal Credentials",
            "insert_after": "parent_company",
            "collaspsible" : 1
        },
        {
            "doctype": "Custom Field",
            "dt": "Company",
            "fieldname": "custom_client_id",
            "fieldtype": "Data",
            "label": "Client ID",
            "insert_after": "custom_portal_credentials",
            "reqd": 0
        },
        {
            "doctype": "Custom Field",
            "dt": "Company",
            "fieldname": "custom_col_01",
            "fieldtype": "Column Break",
            "insert_after": "custom_client_id"
        },
        {
            "doctype": "Custom Field",
            "dt": "Company",
            "fieldname": "custom_client_secret",
            "fieldtype": "Data",
            "label": "Client Secret",
            "insert_after": "custom_col_01",
            "reqd": 0
        }
    ]

    for field in custom_fields:
        try:
            # Check if the custom field already exists
            if not frappe.db.exists("Custom Field", {"dt": field["dt"], "fieldname": field["fieldname"]}):
                # Create and insert the custom field
                frappe.get_doc(field).insert()
                frappe.db.commit()  # Commit the transaction to save the field
        except Exception as e:
            # Log any errors that occur during field creation
            frappe.log_error(f"Failed to create custom field {field['fieldname']}: {str(e)}")
