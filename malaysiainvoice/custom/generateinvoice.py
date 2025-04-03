import frappe
import requests
import urllib.parse
import json
import base64
import hashlib
import xml.etree.ElementTree as ET
# from lxml import etree

@frappe.whitelist(allow_guest=True)
def get_access_token(company):
    TOKEN_URL = "https://preprod-api.myinvois.hasil.gov.my/connect/token"

    if not company.custom_client_id and company.custom.client_secret:
        frappe.throw("Customer Client ID and Client Secret are required.")
    CLIENT_ID = company.custom_client_id
    CLIENT_SECRET = company.custom_client_secret

    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "InvoicingAPI"
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Encode payload properly
    payload_encoded = urllib.parse.urlencode(payload)

    # Send POST request
    response = requests.post(TOKEN_URL, data=payload_encoded, headers=headers)

    # Handle response
    if response.status_code == 200:
        token_data = response.json()
        frappe.response['message'] = token_data["access_token"]
        return token_data["access_token"]
    else:
        frappe.response['message'] = response.text
        return response.text

@frappe.whitelist(allow_guest=True)

def post_sales_invoice(doc):
    """Main method to generate UBL XML, encode it, and submit to LHDN API."""
    sinv = frappe.get_doc("Sales Invoice", doc)
    company = frappe.get_doc("Company", sinv.company)
    invoice_data = generate_invoice_data(doc)
    
    invoice_xml = create_ubl_xml(invoice_data)
    
    # Encode to Base64 and generate SHA-256 hash
    invoice_base64, invoice_hash = encode_invoice(invoice_xml)
    
    # API Endpoint
    INVOICE_URL = "https://preprod-api.myinvois.hasil.gov.my/api/v1.0/documentsubmissions"
    access_token = get_access_token(company)  

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "documents": [
            {
                "format": "XML",
                "documentHash": invoice_hash,
                "codeNumber": str(sinv.name),
                "document": invoice_base64
            }
        ]
    }
    response = requests.post(INVOICE_URL, json=payload, headers=headers)
    msg = ""
    if response.status_code == 202:
        frappe.response['message'] = "✅ Invoice Submitted Successfully"
        msg = "✅ Invoice Submitted Successfully"
        sinv.custom_invoice_status = "Uploaded"
        if response.json().get("acceptedDocuments"):
            sinv.custom_document_uid = response.json()["acceptedDocuments"][0]["uuid"]
        sinv.save()       
    else:
        frappe.response['message'] = response.text
        msg = response.text
    
    frappe.msgprint(f'{msg}')

    # frappe.response['message'] = access_token
    # frappe.response['message'] = {"Invoice Data":invoice_data,"hash " : invoice_hash, "base64 ": invoice_base64, "invoice_xml":invoice_xml}

def generate_invoice_data(doc):
    sinv = frappe.get_doc("Sales Invoice", doc)
    customer = frappe.get_doc("Customer", sinv.customer)
    supplier = frappe.get_doc("Supplier", sinv.custom_supplier)

    total_seconds = int(sinv.posting_time .total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"
    invoice_data = {
        "ID": str(sinv.name),
        "IssueDate": str(sinv.posting_date),
        "IssueTime": str(formatted_time)+"Z",
        "InvoiceTypeCode": "01",
        "DocumentCurrencyCode": str(sinv.currency),
        "TaxCurrencyCode": str(sinv.currency),
        "InvoicePeriod": { # optional
            "StartDate": str(sinv.posting_date),  # Mandatory
            "EndDate": str(sinv.posting_date),    # Mandatory
            "Description": ""# Omit "Description" as it is optional
        },
        "BillingReference": {
            "ID": str(supplier.custom_bill_reference) or "NA"  # Replace with actual PO number
        },
        "AdditionalDocumentReferences": [
            {"ID": "L1", "DocumentType": ""},
            {"ID": "FTA", "DocumentType": "", "DocumentDescription": ""},
            {"ID": "L1", "DocumentType": ""},
            {"ID": "L1"}
        ],
        "AccountingSupplierParty": {
            "AdditionalAccountID": str(supplier.custom_supplier_bank_account),
            "IndustryClassificationCode": str(supplier.custom_misc_code),
            "PartyIdentifications": [
                {"schemeID": "TIN", "ID": str(supplier.custom_tin)},
                {"schemeID": "NRIC", "ID": str(supplier.custom_brn)},
                {"schemeID": "SST", "ID": str(supplier.custom_sst_registration_number) or "NA"},
                {"schemeID": "TTX", "ID": str(supplier.custom_tourism_tax_number) or "NA"}
            ],
            "PostalAddress": {
                # "CityName": "Kuala Lumpur",
                # "PostalZone": "50000",
                # "CountrySubentityCode": "14",
                "AddressLines": [
                    str(supplier.custom_address) or "xyz"
                ],
                "Country": {
                    "IdentificationCode": "MYS"
                }
            },
            "PartyLegalEntity": {
                "RegistrationName": str(supplier.supplier_name)
            },
            "Contact": {
                "Telephone": str(supplier.custom_contact),
                "ElectronicMail": str(supplier.custom_email)
            }
        },
        "AccountingCustomerParty": {
            "PartyIdentifications": [
                {"schemeID": "TIN", "ID": str(customer.custom_tin)},
                {"schemeID": "BRN", "ID": str(customer.custom_registration_identification_passport)},
                {"schemeID": "SST", "ID": str(customer.custom_sst_registration_number) or "NA"},
                {"schemeID": "TTX", "ID": "NA"}
            ],
            "PostalAddress": {
                "CityName": str(customer.custom_city),
                "PostalZone": str(customer.custom_postcode),
                "CountrySubentityCode": str(customer.custom_state),
                "AddressLines": [
                    str(customer.custom_address) or "NA"  # Replace with actual address
                ],
                "Country": {
                    "IdentificationCode": str(customer.custom_country) or "MYS"  # Replace with actual country code
                }
            },
            "PartyLegalEntity": {
                "RegistrationName": str(customer.customer_name)
            },
            "Contact": {
                "Telephone": str(customer.custom_contact),
                "ElectronicMail": str(customer.custom_email),
            }
        },
        "Delivery": { # Optional
            "DeliveryParty": {
                "PartyIdentifications": [
                    {"schemeID": "TIN", "ID": str(customer.custom_tin)},
                    {"schemeID": "BRN", "ID": str(customer.custom_registration_identification_passport)},
                ],
                "PostalAddress": {
                    "CityName": str(customer.custom_city) or "NA",  # Replace with actual city
                    "PostalZone": str(customer.custom_postcode) or "1234567",        # Replace with actual postal code
                    "CountrySubentityCode": str(customer.custom_state) or "14",  # Replace with actual state code
                    "AddressLines": [
                        str(customer.custom_address_line1) or str(customer.custom_address_line2) or str(customer.custom_address_line3) or "NA"   # Replace with actual address
                    ],
                    "Country": {
                        "IdentificationCode": str(customer.custom_country) or "MYS"  # Replace with actual country code
                    }
                },
                "PartyLegalEntity": {
                    "RegistrationName": str(customer.customer_name)  # Replace with actual name
                }
            },
            "Shipment": {
                "ID": str(customer.custom_rip_no) or "SH8975654",  # Replace with actual shipment ID
                "FreightAllowanceCharge": {
                    "ChargeIndicator": "true",  # Mandatory field
                    "AllowanceChargeReason": "Freight Charges",  # Optional
                    "Amount": "1.00"  # Mandatory field
                }
            }
        },
        "PaymentMeans": { # optional
            "PaymentMeansCode": supplier.custom_misc_code,  # Replace with actual payment method code
            "PayeeFinancialAccount": {
                "ID": str(supplier.custom_supplier_bank_account) or "12231324"  # Replace with actual account ID
            }
        },
        "PaymentTerms": { # optional
            "Note": f"Payment method is {supplier.custom_payment_mode}"
        },
        "PrepaidPayment": { # optional and should collect these details from payment entry
            "ID": "PREPAY123",  # Replace with actual prepayment ID(payment entry id)
            "PaidAmount": "0.0", # PE Paid Amount
            "PaidDate":"", # PE posting date
            "PaidTime": "00:12:00Z" # PE posting time
        },
        "AllowanceCharges": [ # this section is optional
            {
                "ChargeIndicator": "false",  # Mandatory field
                "AllowanceChargeReason": "Discount",  # Optional
                "Amount": str(sinv.discount_amount) or "0.0"  # Mandatory field
            },
            {
                "ChargeIndicator": "true",  # Mandatory field
                "AllowanceChargeReason": "Freight Charges",  # Optional
                "Amount": "1.00"  # Mandatory field
            }
        ],
        "TaxTotal": {
            "TaxAmount": str(sinv.total_taxes_and_charges),  # Mandatory field
            "TaxSubtotal": {
                "TaxableAmount": str(sinv.total_taxes_and_charges),  # Mandatory field
                "TaxAmount": str(sinv.total_taxes_and_charges),  # Mandatory field
                "TaxCategory": {
                    "ID": "01",  # Mandatory field
                    "TaxScheme": {
                        "ID": str(sinv.tax_category)
                    }
                }
            }
        },
        "LegalMonetaryTotal": {
            "LineExtensionAmount": str(sinv.total),
            "TaxExclusiveAmount": str(sinv.total),
            "TaxInclusiveAmount": str(sinv.grand_total),
            "AllowanceTotalAmount": str(sinv.base_discount_amount), # optional -- discount total
            "ChargeTotalAmount": str(sinv.grand_total), # optional
            "PayableRoundingAmount": str(sinv.rounding_adjustment), # optional
            "PayableAmount": str(sinv.grand_total)
        },
        "InvoiceLine": []
    }
    for item in sinv.items:
        # Create the invoice line structure
        item_doc = frappe.get_doc("Item", item.item_code)
        invoice_line = {
            "ID": item.item_code,  # Item code
            "InvoicedQuantity": str(item.qty),  # Quantity
            "LineExtensionAmount": str(item.amount),  # Total amount for the line item
            "Item": {
                "Description": str(item.item_name),  # Description of the product/service
                "OriginCountry": {
                    "IdentificationCode": str(customer.custom_country) or "MYS"  # Country of origin
                },
                "CommodityClassification": [
                    {"listID": "PTC", "ItemClassificationCode": str(item_doc.custom_product_tariff_code) or "9800.00.0010"},  # Product tariff code
                    {"listID": "CLASS", "ItemClassificationCode": str(item_doc.custom_classification_code)}  # Classification code
                ]
            },
            "Price": {
                "PriceAmount": str(item.rate),  # Unit price
                "currencyID": str(sinv.currency)  # Currency
            }
        }

        # Add tax details for the current line item
        for tax in sinv.taxes:
            invoice_line["TaxTotal"] = {
                "TaxAmount": str(tax.tax_amount),  # Total tax amount for the line item
                "TaxSubtotal": {
                    "TaxableAmount": str(item.amount),  # Taxable amount for the line item
                    "TaxAmount": str(tax.tax_amount),  # Tax amount for the line item
                    "Percent": str(tax.rate),  # Tax rate (percentage)
                    "TaxCategory": {
                        "ID": "E",  # Tax category code
                        "TaxExemptionReason": "Exempt New Means of Transport",
                        "TaxScheme": {
                            "ID": str(sinv.tax_category)
                        }
                    }
                }
            }

        # Append the invoice line to the InvoiceLine list
        invoice_data["InvoiceLine"].append(invoice_line)
    mandatory ={
        "Supplier":sinv.custom_supplier,
        "TaxScheme": sinv.tax_category,
        "currencyID" : sinv.currency,
        "TaxChargesTemplate":sinv.taxes_and_charges,
        "CustomerTin":customer.custom_tin,
        "CustomerBRN": customer.custom_registration_identification_passport,
        "CustomerName" : customer.customer_name,
        "SupplierName": supplier.supplier_name,
        "SupplierTIN":supplier.custom_tin,
        "SupplierBRN" : supplier.custom_brn
    }
    for field_name, field_value in mandatory.items():
        if not field_value:  # Checks if the field is empty or None
            raise Exception(f"Mandatory field '{field_name}' is missing or empty.")
    return invoice_data

def create_ubl_xml(invoice_data):
    # Create the root element

    currency_id = invoice_data['TaxCurrencyCode']
    namespaces = {
        'xmlns': "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        'xmlns:cac': "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        'xmlns:cbc': "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    }

    # Create the root element with namespaces
    invoice = ET.Element('Invoice', attrib=namespaces)

    # Add basic invoice information
    ET.SubElement(invoice, 'cbc:ID').text = invoice_data['ID']
    ET.SubElement(invoice, 'cbc:IssueDate').text = invoice_data['IssueDate']
    ET.SubElement(invoice, 'cbc:IssueTime').text = invoice_data['IssueTime']
    ET.SubElement(invoice, 'cbc:InvoiceTypeCode', listVersionID="1.0").text = invoice_data['InvoiceTypeCode']
    ET.SubElement(invoice, 'cbc:DocumentCurrencyCode').text = invoice_data['DocumentCurrencyCode']
    ET.SubElement(invoice, 'cbc:TaxCurrencyCode').text = invoice_data['TaxCurrencyCode']

    # Add InvoicePeriod
    # invoice_period = ET.SubElement(invoice, 'cac:InvoicePeriod')
    # ET.SubElement(invoice_period, 'cbc:StartDate').text = invoice_data['InvoicePeriod']['StartDate']
    # ET.SubElement(invoice_period, 'cbc:EndDate').text = invoice_data['InvoicePeriod']['EndDate']
    # ET.SubElement(invoice_period, 'cbc:Description').text = invoice_data['InvoicePeriod']['Description']

    # # Add BillingReference
    # billing_reference = ET.SubElement(invoice, 'cac:BillingReference')
    # billing_reference_line = ET.SubElement(billing_reference, 'cac:BillingReferenceLine')
    # ET.SubElement(billing_reference_line, 'cbc:ID').text = invoice_data['BillingReference']['ID']

    # # Add AdditionalDocumentReferences
    # for doc_ref in invoice_data['AdditionalDocumentReferences']:
    #     additional_doc_ref = ET.SubElement(invoice, 'cac:AdditionalDocumentReference')
    #     ET.SubElement(additional_doc_ref, 'cbc:ID').text = doc_ref['ID']
    #     if 'DocumentType' in doc_ref:
    #         ET.SubElement(additional_doc_ref, 'cbc:DocumentType').text = doc_ref['DocumentType']
    #     if 'DocumentDescription' in doc_ref:
    #         ET.SubElement(additional_doc_ref, 'cbc:DocumentDescription').text = doc_ref['DocumentDescription']

    # Add AccountingSupplierParty
    accounting_supplier_party = ET.SubElement(invoice, 'cac:AccountingSupplierParty')
    ET.SubElement(accounting_supplier_party, 'cbc:AdditionalAccountID', schemeAgencyName="CertEX").text = invoice_data['AccountingSupplierParty']['AdditionalAccountID']
    party = ET.SubElement(accounting_supplier_party, 'cac:Party')
    ET.SubElement(party, 'cbc:IndustryClassificationCode', name="Wholesale of computer hardware, software and peripherals").text = invoice_data['AccountingSupplierParty']['IndustryClassificationCode']
    for party_id in invoice_data['AccountingSupplierParty']['PartyIdentifications']:
        party_identification = ET.SubElement(party, 'cac:PartyIdentification')
        ET.SubElement(party_identification, 'cbc:ID', schemeID=party_id['schemeID']).text = party_id['ID']
    postal_address = ET.SubElement(party, 'cac:PostalAddress')
    #ET.SubElement(postal_address, 'cbc:CityName').text = invoice_data['AccountingSupplierParty']['PostalAddress']['CityName']
    #ET.SubElement(postal_address, 'cbc:PostalZone').text = invoice_data['AccountingSupplierParty']['PostalAddress']['PostalZone']
    #ET.SubElement(postal_address, 'cbc:CountrySubentityCode').text = invoice_data['AccountingSupplierParty']['PostalAddress']['CountrySubentityCode']
    for address_line in invoice_data['AccountingSupplierParty']['PostalAddress']['AddressLines']:
        address_line_element = ET.SubElement(postal_address, 'cac:AddressLine')
        ET.SubElement(address_line_element, 'cbc:Line').text = address_line

    country = ET.SubElement(postal_address, 'cac:Country')
    ET.SubElement(country, 'cbc:IdentificationCode', listAgencyID="6", listID="ISO3166-1").text = invoice_data['AccountingSupplierParty']['PostalAddress']['Country']['IdentificationCode']
    party_legal_entity = ET.SubElement(party, 'cac:PartyLegalEntity')
    ET.SubElement(party_legal_entity, 'cbc:RegistrationName').text = invoice_data['AccountingSupplierParty']['PartyLegalEntity']['RegistrationName']
    contact = ET.SubElement(party, 'cac:Contact')
    ET.SubElement(contact, 'cbc:Telephone').text = invoice_data['AccountingSupplierParty']['Contact']['Telephone']
    ET.SubElement(contact, 'cbc:ElectronicMail').text = invoice_data['AccountingSupplierParty']['Contact']['ElectronicMail']

    # Add AccountingCustomerParty
    accounting_customer_party = ET.SubElement(invoice, 'cac:AccountingCustomerParty')
    party = ET.SubElement(accounting_customer_party, 'cac:Party')
    for party_id in invoice_data['AccountingCustomerParty']['PartyIdentifications']:
        party_identification = ET.SubElement(party, 'cac:PartyIdentification')
        ET.SubElement(party_identification, 'cbc:ID', schemeID=party_id['schemeID']).text = party_id['ID']
    postal_address = ET.SubElement(party, 'cac:PostalAddress')
    ET.SubElement(postal_address, 'cbc:CityName').text = invoice_data['AccountingCustomerParty']['PostalAddress']['CityName']
    ET.SubElement(postal_address, 'cbc:PostalZone').text = invoice_data['AccountingCustomerParty']['PostalAddress']['PostalZone']
    ET.SubElement(postal_address, 'cbc:CountrySubentityCode').text = invoice_data['AccountingCustomerParty']['PostalAddress']['CountrySubentityCode']
    for address_line in invoice_data['AccountingCustomerParty']['PostalAddress']['AddressLines']:
        address_line_element = ET.SubElement(postal_address, 'cac:AddressLine')
        ET.SubElement(address_line_element, 'cbc:Line').text = address_line
    country = ET.SubElement(postal_address, 'cac:Country')
    ET.SubElement(country, 'cbc:IdentificationCode', listAgencyID="6", listID="ISO3166-1").text = invoice_data['AccountingCustomerParty']['PostalAddress']['Country']['IdentificationCode']
    party_legal_entity = ET.SubElement(party, 'cac:PartyLegalEntity')
    ET.SubElement(party_legal_entity, 'cbc:RegistrationName').text = invoice_data['AccountingCustomerParty']['PartyLegalEntity']['RegistrationName']
    contact = ET.SubElement(party, 'cac:Contact')
    ET.SubElement(contact, 'cbc:Telephone').text = invoice_data['AccountingCustomerParty']['Contact']['Telephone']
    ET.SubElement(contact, 'cbc:ElectronicMail').text = invoice_data['AccountingCustomerParty']['Contact']['ElectronicMail']

    # Add Delivery
    # delivery = ET.SubElement(invoice, 'cac:Delivery')
    # delivery_party = ET.SubElement(delivery, 'cac:DeliveryParty')
    # for party_id in invoice_data['Delivery']['DeliveryParty']['PartyIdentifications']:
    #     party_identification = ET.SubElement(delivery_party, 'cac:PartyIdentification')
    #     ET.SubElement(party_identification, 'cbc:ID', schemeID=party_id['schemeID']).text = party_id['ID']
    # postal_address = ET.SubElement(delivery_party, 'cac:PostalAddress')
    # ET.SubElement(postal_address, 'cbc:CityName').text = invoice_data['Delivery']['DeliveryParty']['PostalAddress']['CityName']
    # ET.SubElement(postal_address, 'cbc:PostalZone').text = invoice_data['Delivery']['DeliveryParty']['PostalAddress']['PostalZone']
    # ET.SubElement(postal_address, 'cbc:CountrySubentityCode').text = invoice_data['Delivery']['DeliveryParty']['PostalAddress']['CountrySubentityCode']
    # for address_line in invoice_data['Delivery']['DeliveryParty']['PostalAddress']['AddressLines']:
    #     address_line_element = ET.SubElement(postal_address, 'cac:AddressLine')
    #     ET.SubElement(address_line_element, 'cbc:Line').text = address_line
    # country = ET.SubElement(postal_address, 'cac:Country')
    # ET.SubElement(country, 'cbc:IdentificationCode', listAgencyID="6", listID="ISO3166-1").text = invoice_data['Delivery']['DeliveryParty']['PostalAddress']['Country']['IdentificationCode']
    # party_legal_entity = ET.SubElement(delivery_party, 'cac:PartyLegalEntity')
    # ET.SubElement(party_legal_entity, 'cbc:RegistrationName').text = invoice_data['Delivery']['DeliveryParty']['PartyLegalEntity']['RegistrationName']
    # shipment = ET.SubElement(delivery, 'cac:Shipment')
    # ET.SubElement(shipment, 'cbc:ID').text = invoice_data['Delivery']['Shipment']['ID']
    # freight_allowance_charge = ET.SubElement(shipment, 'cac:FreightAllowanceCharge')
    # ET.SubElement(freight_allowance_charge, 'cbc:ChargeIndicator').text = invoice_data['Delivery']['Shipment']['FreightAllowanceCharge']['ChargeIndicator']
    # ET.SubElement(freight_allowance_charge, 'cbc:AllowanceChargeReason').text = invoice_data['Delivery']['Shipment']['FreightAllowanceCharge']['AllowanceChargeReason']
    # ET.SubElement(freight_allowance_charge, 'cbc:Amount', currencyID=currency_id).text = invoice_data['Delivery']['Shipment']['FreightAllowanceCharge']['Amount']

    # # Add PaymentMeans
    # payment_means = ET.SubElement(invoice, 'cac:PaymentMeans')
    # ET.SubElement(payment_means, 'cbc:PaymentMeansCode').text = invoice_data['PaymentMeans']['PaymentMeansCode']
    # payee_financial_account = ET.SubElement(payment_means, 'cac:PayeeFinancialAccount')
    # ET.SubElement(payee_financial_account, 'cbc:ID').text = invoice_data['PaymentMeans']['PayeeFinancialAccount']['ID']

    # # Add PaymentTerms
    # payment_terms = ET.SubElement(invoice, 'cac:PaymentTerms')
    # ET.SubElement(payment_terms, 'cbc:Note').text = invoice_data['PaymentTerms']['Note']

    # # Add PrepaidPayment
    # prepaid_payment = ET.SubElement(invoice, 'cac:PrepaidPayment')
    # ET.SubElement(prepaid_payment, 'cbc:ID').text = invoice_data['PrepaidPayment']['ID']
    # ET.SubElement(prepaid_payment, 'cbc:PaidAmount', currencyID=currency_id).text = invoice_data['PrepaidPayment']['PaidAmount']
    # ET.SubElement(prepaid_payment, 'cbc:PaidDate').text = invoice_data['PrepaidPayment']['PaidDate']
    # ET.SubElement(prepaid_payment, 'cbc:PaidTime').text = invoice_data['PrepaidPayment']['PaidTime']

    # # Add AllowanceCharges
    # for allowance_charge in invoice_data['AllowanceCharges']:
    #     allowance_charge_element = ET.SubElement(invoice, 'cac:AllowanceCharge')
    #     ET.SubElement(allowance_charge_element, 'cbc:ChargeIndicator').text = allowance_charge['ChargeIndicator']
    #     ET.SubElement(allowance_charge_element, 'cbc:AllowanceChargeReason').text = allowance_charge['AllowanceChargeReason']
    #     ET.SubElement(allowance_charge_element, 'cbc:Amount', currencyID=currency_id).text = allowance_charge['Amount']

    # Add TaxTotal
    tax_total = ET.SubElement(invoice, 'cac:TaxTotal')
    ET.SubElement(tax_total, 'cbc:TaxAmount', currencyID=currency_id).text = invoice_data['TaxTotal']['TaxAmount']
    tax_subtotal = ET.SubElement(tax_total, 'cac:TaxSubtotal')
    ET.SubElement(tax_subtotal, 'cbc:TaxableAmount', currencyID=currency_id).text = invoice_data['TaxTotal']['TaxSubtotal']['TaxableAmount']
    ET.SubElement(tax_subtotal, 'cbc:TaxAmount', currencyID=currency_id).text = invoice_data['TaxTotal']['TaxSubtotal']['TaxAmount']
    tax_category = ET.SubElement(tax_subtotal, 'cac:TaxCategory')
    ET.SubElement(tax_category, 'cbc:ID').text = invoice_data['TaxTotal']['TaxSubtotal']['TaxCategory']['ID']
    tax_scheme = ET.SubElement(tax_category, 'cac:TaxScheme')
    ET.SubElement(tax_scheme, 'cbc:ID', schemeAgencyID="6", schemeID="UN/ECE 5153").text = invoice_data['TaxTotal']['TaxSubtotal']['TaxCategory']['TaxScheme']['ID']

    # Add LegalMonetaryTotal
    legal_monetary_total = ET.SubElement(invoice, 'cac:LegalMonetaryTotal')
    ET.SubElement(legal_monetary_total, 'cbc:LineExtensionAmount', currencyID=currency_id).text = invoice_data['LegalMonetaryTotal']['LineExtensionAmount']
    ET.SubElement(legal_monetary_total, 'cbc:TaxExclusiveAmount', currencyID=currency_id).text = invoice_data['LegalMonetaryTotal']['TaxExclusiveAmount']
    ET.SubElement(legal_monetary_total, 'cbc:TaxInclusiveAmount', currencyID=currency_id).text = invoice_data['LegalMonetaryTotal']['TaxInclusiveAmount']
    ET.SubElement(legal_monetary_total, 'cbc:AllowanceTotalAmount', currencyID=currency_id).text = invoice_data['LegalMonetaryTotal']['AllowanceTotalAmount']
    ET.SubElement(legal_monetary_total, 'cbc:ChargeTotalAmount', currencyID=currency_id).text = invoice_data['LegalMonetaryTotal']['ChargeTotalAmount']
    ET.SubElement(legal_monetary_total, 'cbc:PayableRoundingAmount', currencyID=currency_id).text = invoice_data['LegalMonetaryTotal']['PayableRoundingAmount']
    ET.SubElement(legal_monetary_total, 'cbc:PayableAmount', currencyID=currency_id).text = invoice_data['LegalMonetaryTotal']['PayableAmount']

    for item in invoice_data['InvoiceLine']:
        # Create the InvoiceLine element
        invoice_line = ET.SubElement(invoice, 'cac:InvoiceLine')

        # Add ID, InvoicedQuantity, and LineExtensionAmount
        ET.SubElement(invoice_line, 'cbc:ID').text = item['ID']
        ET.SubElement(invoice_line, 'cbc:InvoicedQuantity', unitCode="C62").text = item['InvoicedQuantity']
        ET.SubElement(invoice_line, 'cbc:LineExtensionAmount', currencyID="MYR").text = item['LineExtensionAmount']

        # Add TaxTotal (if exists)
        if 'TaxTotal' in item:
            tax_total = ET.SubElement(invoice_line, 'cac:TaxTotal')
            ET.SubElement(tax_total, 'cbc:TaxAmount', currencyID="MYR").text = item['TaxTotal']['TaxAmount']

            tax_subtotal = ET.SubElement(tax_total, 'cac:TaxSubtotal')
            ET.SubElement(tax_subtotal, 'cbc:TaxableAmount', currencyID="MYR").text = item['TaxTotal']['TaxSubtotal']['TaxableAmount']
            ET.SubElement(tax_subtotal, 'cbc:TaxAmount', currencyID="MYR").text = item['TaxTotal']['TaxSubtotal']['TaxAmount']
            ET.SubElement(tax_subtotal, 'cbc:Percent').text = item['TaxTotal']['TaxSubtotal']['Percent']

            tax_category = ET.SubElement(tax_subtotal, 'cac:TaxCategory')
            ET.SubElement(tax_category, 'cbc:ID').text = item['TaxTotal']['TaxSubtotal']['TaxCategory']['ID']
            ET.SubElement(tax_category, 'cbc:TaxExemptionReason').text = item['TaxTotal']['TaxSubtotal']['TaxCategory'].get('TaxExemptionReason', '')

            tax_scheme = ET.SubElement(tax_category, 'cac:TaxScheme')
            ET.SubElement(tax_scheme, 'cbc:ID', schemeAgencyID="6", schemeID="UN/ECE 5153").text = item['TaxTotal']['TaxSubtotal']['TaxCategory']['TaxScheme']['ID']

        # Add Item details
        item_element = ET.SubElement(invoice_line, 'cac:Item')
        ET.SubElement(item_element, 'cbc:Description').text = item['Item']['Description']

        # Add OriginCountry
        origin_country = ET.SubElement(item_element, 'cac:OriginCountry')
        ET.SubElement(origin_country, 'cbc:IdentificationCode').text = item['Item']['OriginCountry']['IdentificationCode']

        # Add CommodityClassifications
        for commodity_classification in item['Item'].get('CommodityClassification', []):
            commodity_classification_element = ET.SubElement(item_element, 'cac:CommodityClassification')
            ET.SubElement(
                commodity_classification_element,
                'cbc:ItemClassificationCode',
                listID=commodity_classification.get('listID', '')
            ).text = commodity_classification.get('ItemClassificationCode', '')

        # Add Price
        price_element = ET.SubElement(invoice_line, 'cac:Price')
        ET.SubElement(price_element, 'cbc:PriceAmount', currencyID="MYR").text = item['Price']['PriceAmount']

    # Convert the XML tree to a string
    xml_str = ET.tostring(invoice, encoding='unicode', method='xml')
    return xml_str



def encode_invoice(invoice_xml):
    """Encodes the XML invoice to Base64 and generates SHA-256 hash."""
    
    invoice_base64 = base64.b64encode(invoice_xml.encode()).decode()
    # Compute SHA-256 hash of the raw XML content
    invoice_hash = hashlib.sha256(invoice_xml.encode()).hexdigest()
    
    return invoice_base64, invoice_hash


@frappe.whitelist(allow_guest=True)
def cancel_invoice(invoice_id, reason):
    sinv = frappe.get_doc("Sales Invoice", invoice_id)
    company = frappe.get_doc("Company", sinv.company)
    access_token = get_access_token(company)

    # Construct the API URL
    INVOICE_URL = f"https://preprod-api.myinvois.hasil.gov.my/api/v1.0/documents/state/{sinv.custom_document_uid}/state"
    # access_token = get_access_token()  

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "status":"cancelled",
        "reason": str(reason)
    }

    response = requests.put(INVOICE_URL, json=payload, headers=headers)
    msg = ""
    if response.status_code == 200:
        frappe.response['message'] = "✅ Invoice Cancelled Successfully"
        msg = "✅ Invoice Cancelled Successfully"
        sinv.custom_invoice_status = "Cancelled"
        sinv.cancel()
    else:
        frappe.response['message'] = response.text
        msg = response.text
    frappe.msgprint(f'{msg}')
