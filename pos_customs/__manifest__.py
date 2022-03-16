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
        'web.assets_qweb': [
        ],
        'web._assets_primary_variables': [
        ],s
        'web._assets_backend_helpers': [
        ],
        'web.assets_backend': [
        ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3'
}
