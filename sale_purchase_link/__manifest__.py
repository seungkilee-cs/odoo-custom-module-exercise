# -*- coding: utf-8 -*-
{
    "name": "Sale Purchase Link",
    "version": "19.0.1.0.0",
    "category": "Sales/Purchase",
    "summary": "Custom Module - Create Purchase Orders from Sales Orders + smart navigation",
    "description": """
- "Create Purchase Order" on Sales Orders (creates an RFQ from SO lines).
- A link between PO and SO.
- Smart buttons to navigate SO <-> PO.
""",
    "author": "Seung Ki Lee",
    "depends": ["sale_management", "purchase"],
    "data": [
        "views/sale_order_views.xml",
        "views/purchase_order_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
