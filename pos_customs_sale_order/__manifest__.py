# -*- coding: utf-8 -*-
{
    "name": "Point of sale Customs",
    'version': '0.01b',
    'author': '@glopzvega',
    'website': 'https://github.com/glopzvega',
    "depends": [
        "base",
        "point_of_sale",
        "pos_sale",
    ],
    "data": [
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_customs_sale_order/static/src/js/SaleOrderFetcher.js'
        ],
        'web.assets_qweb': [
        ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3'
}
