# -*- coding: utf-8 -*-
{
    'name': "cost_serial_numer",

    'summary': """
        Toma el costo del producto dependiendo el numero de serie""",

    'description': """
        Toma el costo del producto dependiendo el numero de serie
    """,

    'author': "Gerardo A Lopez Vega",
    'website': "http://www.iozoft.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Purchases',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sales', 'purchase', 'stock', 'purchase_stock', 'inventory_customs'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}