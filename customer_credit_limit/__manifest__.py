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
                'account'],
    "data": [
        'security/groups.xml',
        'views/sale_view_inherit.xml',
        'views/res_partner_inherit.xml',
        'data/mail_template.xml'

    ],
    'assets': {
        'point_of_sale.assets': [

        ],
        'web.assets_qweb': [
            'pos_sale/static/src/xml/SaleOrderList.xml',
        ],
    },
    "auto_install": False,
    "installable": True,
    "category": "Sales",
}