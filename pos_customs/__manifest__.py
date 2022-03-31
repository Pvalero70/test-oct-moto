# -*- coding: utf-8 -*-
{
    "name": "Point of sale Customs",
    'version': '0.01b',
    'author': 'Ing. Isaac Chávez Arroyo',
    'website': 'https://isaaccv.ml',
    "depends": ["base", "point_of_sale", "l10n_mx_edi"],
    "data": [
        'views/pos_conf_views.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_customs/static/src/css/payment_screen.css',
            'pos_customs/static/src/js/payment_screen.js',
        ],
        'web.assets_qweb': [
            'pos_customs/static/src/xml/payment_screen.xml',
            'pos_customs/static/src/xml/pos_receipt.xml',
        ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3'
}
