# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Point of Sale Custom Settle Due',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'summary': "Settle custumer's invoice due in the POS UI.",
    'description': """""",
    'depends': ['pos_settle_due', 'pos_customs'],
    'data': [],
    'demo': [],
    'installable': True,
    'auto_install': True,
    'license': 'OEEL-1',
    'assets': {
        'point_of_sale.assets': [
            'pos_custom_settle_due/static/src/css/**/*.css',
            'pos_custom_settle_due/static/src/js/**/*.js',
        ],
        'web.assets_qweb': [
            'pos_custom_settle_due/static/src/xml/**/*.xml',
        ],
    }
}