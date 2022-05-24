# -*- coding: utf-8 -*-
# Copyright 2022 - QUADIT, SA DE CV(https://www.quadit.mx)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Plugin for repairs and product releases',
    'version': '15.0.1',
    'author': 'Quadit',
    'category': 'Repair',
    'website': "https://www.quadit.mx",
    'support': 'support@quadit.mx',
    'summary': 'Plugin for repairs and product releases',
    'license': 'LGPL-3',
    'depends': [
        'l10n_mx_edi','repair'
    ],
    'data': [
        'views/repair_order.xml',
    ],
    'demo': [
    ],
    'maintainers': [
        'gerardomr8'
    ],
    'installable': True,
    'auto_install': False,
}