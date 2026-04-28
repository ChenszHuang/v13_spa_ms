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
        "account",
        ],

    "data": [
        #security
        "security/security.xml",
        "security/ir.model.access.csv",
        
        #data
        "data/admin_data.xml",
        "data/sequence.xml",
        "data/cron_data.xml",
        "data/report_paperformat_data.xml",

        #report
        "reports/layout_report.xml",
        "reports/revenue_report.xml",
        "reports/receipt_report.xml",
        "reports/therapist_activity_report.xml",

        #views
        "views/spa_order_views.xml",
        "views/spa_session_views.xml",
        "views/partner_views.xml",
        "views/product_views.xml",
        "views/account_move.xml",
        "views/account_payment.xml",
        "wizards/print_revenue_report.xml",
        "wizards/print_therapist_activity_report.xml",


        "views/menu_views.xml",
        "views/company_views.xml",


        
    ],

    "installable": True,
    "application": True,
}