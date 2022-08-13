# -*- coding: utf-8 -*-
{
    "name": "Sellers commissions",
    'version': '0.01b',
    'author': 'Ing. Isaac Chávez Arroyo',
    'website': 'https://isaaccv.ml',
    "depends": [
        "base",
        "sale",
        "repair"
    ],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/seller_commission.xml",
        "views/invoice.xml"
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
