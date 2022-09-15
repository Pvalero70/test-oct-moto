# -*- coding: utf-8 -*-

# Copyright © 2018 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (<support@garazd.biz>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    'name': 'Restricciones de precio en productos',
    'version': '15.0.1.0.1',
    'category': 'Ventas',
    'author': 'Ing. Alejandro Garcia Magaña',
    'website': '',
    'license': 'LGPL-3',
    'summary': 'Restricciones de precio de productos',

    'depends': [
        'account',
        'pos_sale',
        'repair',

    ],
    'data': [
        'security/product_price_security.xml',
        'views/product_price_views.xml'

    ],
    'demo': [],
    'external_dependencies': {
    },

    'support': 'support@garazd.biz',
    'application': False,
    'installable': True,
    'auto_install': False,
}
