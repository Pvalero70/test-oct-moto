# -*- coding: utf-8 -*-
{
    'name': "importa_xml_cfdis",

    'summary': """
        Importa CFDIs en formato XML para validar pedidos de compra""",

    'description': """
        Importa CFDIs en formato XML para validar pedidos de compra
    """,

    'author': "Gerardo A Lopez Vega",
    'website': "http://www.iozoft.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Purchases',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['purchase', 'stock', 'purchase_stock'],

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