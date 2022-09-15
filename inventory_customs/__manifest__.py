# -*- coding: utf-8 -*-
{
    "name": "Inventory Customs",
    'version': '0.01b',
    'author': 'Ing. Isaac Chávez Arroyo',
    'website': 'https://isaaccv.ml',
    "depends": ["base", "product", "stock", "sale", "stock_account"],
    "data": [
        "security/groups.xml",
        'security/ir.model.access.csv',
        'views/product_product.xml',
        'views/product_brand.xml',
        'views/stock_views.xml',
        'views/res_company.xml',
        'views/sale_order.xml',
        'reports/invoice.xml',
    ],
    'assets': {
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3'
}
