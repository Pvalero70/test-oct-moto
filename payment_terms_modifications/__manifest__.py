# -*- coding: utf-8 -*-

# Copyright © 2018 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (<support@garazd.biz>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    'name': 'Modificaciones en Terminos de Pago',
    'version': '15.0.1.0.1',
    'category': 'sale',
    'author': 'Ing. Alejandro Garcia Magaña',
    'website': '',
    'license': 'LGPL-3',
    'summary': 'Modificaciones en Terminos de Pago en partners, ventas y en punto de venta ',

    'depends': [
        'base',

    ],
    'data': [
        'payment_terms_modifications/security/payment_term_security.xml',
        'views/res_partner_views.xml',


    ],
    'demo': [],
    'external_dependencies': {
    },
    'support': 'support@garazd.biz',
    'application': True,
    'installable': True,
    'auto_install': False,
}
