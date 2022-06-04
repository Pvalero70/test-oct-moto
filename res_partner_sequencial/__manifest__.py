# -*- coding: utf-8 -*-

# Copyright © 2018 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (<support@garazd.biz>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    'name': 'Numero Sequencial Contactos',
    'version': '15.0.1.0.1',
    'category': 'Contactos',
    'author': 'Ing. Alejandro Garcia Magaña',
    'website': '',
    'license': 'LGPL-3',
    'summary': 'Modificaciones en reportes de inventario',

    'depends': [
        'sale',
        'purchase',
        'base',
    ],
    'data': [
        'views/res_partner_sequence.xml',
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
