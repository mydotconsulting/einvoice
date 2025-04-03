import frappe

def execute():
    custom_fields = [
        {
            "doctype": "Custom Field",
            "dt": "Item",  # DocType to which the field is added
            "fieldname": "custom_classification_code",
            "fieldtype": "Data",
            "label": "Classification Code",
            "insert_after": "stock_uom",  # Field after which this custom field will be inserted
            "reqd": 1,  # Mandatory field
        },
        {
            "doctype": "Custom Field",
            "dt": "Item",  # DocType to which the field is added
            "fieldname": "custom_product_service_description",
            "fieldtype": "Data",
            "label": "Description of Product or Services",
            "insert_after": "custom_classification_code",  # Field after which this custom field will be inserted
            "reqd": 1,  # Mandatory field
        },
        {
            "doctype": "Custom Field",
            "dt": "Item",
            "fieldname": "custom_product_tariff_code",
            "fieldtype": "Data",
            "label": "Product Tariff Code",
            "insert_after": "custom_product_service_description",  # Field after which this custom field will be inserted
            "reqd": 0,  # Not mandatory
        },
        {
            "doctype": "Custom Field",
            "dt": "Item",
            "fieldname": "custom_measurement",
            "fieldtype": "Data",
            "label": "Measurement",
            "insert_after": "custom_product_tariff_code", 
            "reqd": 0, 
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
