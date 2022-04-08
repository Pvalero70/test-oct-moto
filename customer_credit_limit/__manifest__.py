# -*- coding: utf-8 -*-

{
    "name": "Customer Credit Limit",
    "author": "Ing. Isaac Chávez",
    "version": "14.0.1.0",
    "description": """
    """,
    "license": 'LGPL-3',
    "depends": ['base',
                'sale_management',
                'account',
                'stock',
                'sale_stock'],
    "data": [
        'security/groups.xml',
        'views/config_views.xml',
        'views/sale_view_inherit.xml',
        'views/res_partner_inherit.xml',
        'views/picking_inherit_view.xml',
        
    ],
    "auto_install": False,
    "installable": True,
    "category": "Sales",
}