# -*- coding: utf-8 -*-
{
    "name": "Bank commissions",
    'version': '0.01b',
    'author': 'Ing. Isaac Chávez Arroyo',
    'website': 'https://isaaccv.ml',
    "depends": [
        "base", "point_of_sale"
    ],
    "data": [
        # 'data/product_commission.xml',
        'views/pos.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
        ],
        'web.assets_qweb': [
        ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3'
}
