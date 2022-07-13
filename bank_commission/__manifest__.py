# -*- coding: utf-8 -*-
{
    "name": "Bank commissions",
    'version': '0.01b',
    'author': 'Ing. Isaac Chávez Arroyo',
    'website': 'https://isaaccv.ml',
    "depends": [
        "base", "point_of_sale", "pos_customs"
    ],
    "data": [
        'data/product_commission.xml',
        'views/pos.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'bank_commission/static/src/js/PaymentScreen.js',
            'bank_commission/static/src/js/PaymentScreenStatusBc.js',
            'bank_commission/static/src/js/ProductScreen.js',
            'bank_commission/static/src/js/PaymentScreenPaymentBc.js'
        ],
        'web.assets_qweb': [
            'bank_commission/static/src/xml/PaymentScreenPaymentLineBc.xml',
        ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3'
}
