# -*- coding: utf-8 -*-

# Copyright © 2018 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (<support@garazd.biz>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    'name': 'Restricciones de notas de credito',
    'version': '15.0.1.0.1',
    'category': 'Ventas',
    'author': 'Ing. Alejandro Garcia Magaña',
    'website': '',
    'license': 'LGPL-3',
    'summary': 'Restricciones de contabilidad',

    'depends': [
        'account',
        'pos_sale',
        'pos_settle_due',
        'point_of_sale',
    ],
    'data': [
        'security/credit_note_security.xml',
        'security/ir.model.access.csv',
        'views/product_category_views.xml',
    ],
    'demo': [],
    'external_dependencies': {
    },
    'assets': {
        'point_of_sale.assets': [
            'credit_note_restrict/static/src/js/RefundButtonHide.js',
        ],

    },
    'support': 'support@garazd.biz',
    'application': False,
    'installable': True,
    'auto_install': False,
}
