# -*- coding: utf-8 -*-
{
    "name": "Inventory Customs",
    'version': '0.01b',
    'author': 'Ing. Isaac Chávez Arroyo',
    'website': 'https://isaaccv.ml',
    "depends": ["base", "product", "stock"],
    "data": [
        'security/ir.model.access.csv',
        'views/product_product.xml',
        'views/product_brand.xml',
    ],
    'assets': {
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3'
}
