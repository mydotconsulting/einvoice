import frappe

def execute():
    custom_fields = [
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_tax_setcion_details",
            "fieldtype": "Section Break",
            "label": "Tax Details",
            "insert_after": "image",
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_tin",
            "fieldtype": "Data",
            "label": "TIN",
            "insert_after": "custom_tax_setcion_details",
            "reqd": 0
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_tid_type",
            "fieldtype": "Select",
            "label": "ID Type",
            "insert_after": "custom_tin",
            "reqd": 1,
            "options": "\nIdentification Card No\nPassport No\nBusiness Registration No\nArmy No"
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_registration_identification_passport",
            "fieldtype": "Data",
            "label": "Registration/Identification/Passport",
            "insert_after": "custom_tid_type",
            "reqd": 1
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_col_01",
            "fieldtype": "Column Break",
            "insert_after": "custom_registration_identification_passport"
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_sst_registration_number",
            "fieldtype": "Data",
            "label": "SST Registration Number",
            "insert_after": "custom_col_01",
            "reqd": 0,
            "default": "N/A"
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_email",
            "fieldtype": "Data",
            "label": "Email",
            "insert_after": "custom_sst_registration_number", 
            "unique": 1
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_address",
            "fieldtype": "Data",
            "label": "Address",
            "insert_after": "custom_email"
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_contact",
            "fieldtype": "Data",
            "label": "Contact",
            "insert_after": "custom_address"
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_shipping_details",
            "fieldtype": "Section Break",
            "label": "Shipping Details",
            "insert_after": "custom_contact"
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_receipients_name",
            "fieldtype": "Data",
            "label": "Shipping Recipient's Name",
            "insert_after": "custom_shipping_details",
            "reqd": 0
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_address_line1",
            "fieldtype": "Data",
            "label": "Address Line 1",
            "insert_after": "custom_receipients_name"
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_address_line2",
            "fieldtype": "Data",
            "label": "Address Line 2",
            "insert_after": "custom_address_line1"
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_address_line3",
            "fieldtype": "Data",
            "label": "Address Line 3",
            "insert_after": "custom_address_line2"
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_col_03",
            "fieldtype": "Column Break",
            "insert_after": "custom_address_line3",
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_postcode",
            "fieldtype": "Data",
            "label": "Postcode",
            "insert_after": "custom_col_03"
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_city",
            "fieldtype": "Data",
            "label": "City",
            "insert_after": "custom_postcode"
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_country",
            "fieldtype": "Data",
            "label": "Country",
            "insert_after": "custom_city"
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_col_04",
            "fieldtype": "Column Break",
            "insert_after": "custom_country"
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_state",
            "fieldtype": "Data",
            "label": "State",
            "insert_after": "custom_col_04"
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_id_type",
            "fieldtype": "Select",
            "label": "Recipient ID Type",
            "options": "\nIdentification Card No\nPassport No\nBusiness Registration No\nArmy No",
            "insert_after": "custom_state"
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_rip_no",
            "fieldtype": "Data",
            "label": "Registration/Identification/Passport Number",
            "insert_after": "custom_id_type"
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_portal_credentials",
            "fieldtype": "Section Break",
            "label": "Portal Credentials",
            "insert_after": "custom_rip_no",
            "collaspsible" : 1
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_client_id",
            "fieldtype": "Data",
            "label": "Client ID",
            "insert_after": "custom_portal_credentials",
            "reqd": 0
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_col_05",
            "fieldtype": "Column Break",
            "insert_after": "custom_client_id"
        },
        {
            "doctype": "Custom Field",
            "dt": "Customer",
            "fieldname": "custom_client_secret",
            "fieldtype": "Data",
            "label": "Client Secret",
            "insert_after": "custom_col_05",
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
