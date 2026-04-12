{
    "name": "Spa Management System",
    "version": "1.0",
    "summary": "Spa Order and Session Management",
    "description": """
        Custom module for managing spa operations:
        - Spa Order (header)
        - Spa Session (per customer / therapist)
        - Basic foundation for invoicing and scheduling
    """,
    "author":"Chensz",

    "depends": [
        "base",
        "contacts",
        "product",
        "account"
        ],

    "data": [
        #security
        "security/security.xml",
        "security/ir.model.access.csv",

        #views
        "views/spa_order_views.xml",
        "views/spa_session_views.xml",
        "views/partner_views.xml",
        "views/menu_views.xml",
        
    ],

    "installable": True,
    "application": True,
}