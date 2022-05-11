# -*- coding: utf-8 -*-

# Copyright © 2018 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (<support@garazd.biz>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    'name': 'Discount of POS Order ',
    'version': '15.0.1.0.1',
    'category': 'Ventas',
    'author': 'Ing. Alejandro Garcia Magaña',
    'website': '',
    'license': 'LGPL-3',
    'summary': 'Only allowed pos order restrictions',

    'depends': [
        'sale',
        'pos_sale',
    ],
    'data': [
        'security/user_discount_security.xml',
        'security/ir.model.access.csv',
        'views/res_users_discount_views.xml',
    ],
    'demo': [],
    'external_dependencies': {
    },
    'support': 'support@garazd.biz',
    'application': False,
    'installable': True,
    'auto_install': False,
}
