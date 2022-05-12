# -*- coding: utf-8 -*-
{
    "name": "Point of sale Customs",
    'version': '0.01b',
    'author': 'Ing. Isaac Chávez Arroyo',
    'website': 'https://isaaccv.ml',
    "depends": [
        "base",
        "point_of_sale",
        "l10n_mx_edi",
        "pos_sale",
    ],
    "data": [
        'views/pos_conf_views.xml',
        'views/pos_order.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_customs/static/src/css/payment_screen.css',
            'pos_customs/static/src/css/pos.css',
            'pos_customs/static/src/js/payment_screen.js',
            'pos_customs/static/src/js/orderReceipt.js',
            'pos_customs/static/src/js/ClientListScreen.js',
            'pos_customs/static/src/js/ClientLine.js'
        ],
        'web.assets_qweb': [
            'pos_customs/static/src/xml/payment_screen.xml',
            'pos_customs/static/src/xml/pos_receipt.xml',
            'pos_customs/static/src/xml/templates.xml',
        ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3'
}
