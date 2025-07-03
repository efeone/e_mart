from frappe import _

def get_data(data=None):
    return {
        "fieldname": "purchase_invoice",  
        "non_standard_fieldnames": {
            "Debit Note Log": "purchase_invoice"
        },
        "transactions": [
            {
                "items": ["Debit Note Log"]
            }
        ]
    }
