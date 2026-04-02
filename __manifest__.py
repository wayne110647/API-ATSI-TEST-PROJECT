{
    'name': 'Master Data API',
    'version': '17.0.1.0.0',
    'summary': 'API Controller for creating Master Data (Customer, Vendor, Product, Employee, COA)',
    'description': """
        This module provides API endpoints to create master data in Odoo.
        Endpoints:
        - /master_api/create/customer
        - /master_api/create/vendor
        - /master_api/create/product
        - /master_api/create/employee
        - /master_api/create/coa
    """,
    'category': 'Tools',
    'author': 'Antigravity',
    'depends': ['base', 'sale', 'purchase', 'stock', 'hr', 'account'],
    'data': [
        # Security access might be needed if we use a custom model, but we are using standard models.
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
