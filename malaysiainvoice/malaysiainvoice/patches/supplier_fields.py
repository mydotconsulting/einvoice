
import frappe

def execute():
    custom_fields = [
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_tax_setcion_details",
            "fieldtype": "Section Break",
            "label": "Tax Details",
            "insert_after": "image"
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_tin",
            "fieldtype": "Data",
            "label": "TIN",
            "insert_after": "custom_tax_setcion_details",
            "reqd": 0
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_brn",
            "fieldtype": "Data",
            "label": "BRN",
            "insert_after": "custom_tin"
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_misc_code",
            "fieldtype": "Data",
            "label": "MISC Code",
            "insert_after": "custom_brn",
            "reqd": 1
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_col_01",
            "fieldtype": "Column Break",
            "insert_after": "custom_misc_code"
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_business_activity_description",
            "fieldtype": "Data",
            "label": "Business Activity Description",
            "insert_after": "custom_col_01",
            "reqd": 1
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_sst_registration_number",
            "fieldtype": "Data",
            "label": "SST Registration Number",
            "insert_after": "custom_business_activity_description",
            "reqd": 0,
            "default": "N/A"
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_col_02",
            "fieldtype": "Column Break",
            "insert_after": "custom_sst_registration_number",
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_tourism_tax_number",
            "fieldtype": "Data",
            "label": "Tourism Tax Number",
            "insert_after": "custom_col_02",
            "reqd": 0,
            "default": "N/A"
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_email",
            "fieldtype": "Data",
            "label": "Email",
            "insert_after": "custom_tourism_tax_number", 
            "unique": 1
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_address",
            "fieldtype": "Data",
            "label": "Address",
            "insert_after": "custom_email"
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_contact",
            "fieldtype": "Data",
            "label": "Contact",
            "insert_after": "custom_address", 
            "unique": 1
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_payment_setcion_details",
            "fieldtype": "Section Break",
            "label": "Payment and Prepayment Information",
            "insert_after": "custom_contact",
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_payment_mode",
            "fieldtype": "Select",
            "label": "Payment Mode",
            "options": "\nBankTransfer\nCashCheque\nCredit Card\nDebit Card\nDigital Bank e-wallet\nDigital Wallet\nOthers",
            "insert_after": "custom_payment_setcion_details"
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_supplier_bank_account",
            "fieldtype": "Link",
            "label": "Supplier's Bank Account",
            "options": "Account",
            "insert_after": "custom_payment_mode"
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_col_06",
            "fieldtype": "Column Break",
            "insert_after": "custom_supplier_bank_account"
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_prepayment_amount",
            "fieldtype": "Float",
            "label": "Prepayment Amount",
            "insert_after": "custom_col_06"
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_prepayment_date",
            "fieldtype": "Date",
            "label": "Prepayment Date",
            "default" : "Today",
            "insert_after": "custom_prepayment_amount"
        },
        {
            "doctype": "Custom Field",
            "dt": "Supplier",
            "fieldname": "custom_bill_reference",
            "fieldtype": "Data",
            "label": "Bill Reference",
            "insert_after": "custom_prepayment_date"
        }
    ]

    for field in custom_fields:
        try:
            if not frappe.db.exists("Custom Field", {"dt": field["dt"], "fieldname": field["fieldname"]}):
                frappe.get_doc(field).insert()
                frappe.db.commit()  # Commit after each successful insertion
        except Exception as e:
            frappe.log_error(f"Failed to create custom field {field['fieldname']}: {str(e)}")
