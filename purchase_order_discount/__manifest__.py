# -*- coding: utf-8 -*-

# Copyright © 2018 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (<support@garazd.biz>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    'name': 'Descuento en Compras',
    'version': '15.0.1.0.1',
    'category': 'Compras',
    'author': 'Ing. Alejandro Garcia Magaña',
    'website': '',
    'license': 'LGPL-3',
    'summary': 'Descuentos en las solicitudes de cotizacion en las compras',

    'depends': [
        'account',
        'purchase',
    ],
    'data': [
        'security/user_discount_security.xml',
        'views/purchase_line_discount_view.xml',
        'report/sol_cotizacion_inherit_template.xml',
    ],
    'demo': [],
    'external_dependencies': {
    },
    'support': 'support@garazd.biz',
    'application': True,
    'installable': True,
    'auto_install': False,
}
