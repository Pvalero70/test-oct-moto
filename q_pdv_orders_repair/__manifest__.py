# -*- coding: utf-8 -*-
# Copyright 2022 - QUADIT, SA DE CV(https://www.quadit.mx)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Plugin for PdV',
    'version': '15.0.1',
    'author': 'Quadit',
    'category': 'Repair',
    'website': "https://www.quadit.mx",
    'support': 'support@quadit.mx',
    'summary': 'Plugin for PdV',
    'license': 'LGPL-3',
    'depends': [
        'l10n_mx_edi','repair','point_of_sale', 'pos_sale'
    ],
    'data': [
        'views/repair_order.xml',
        'views/pos_order.xml',
    ],
    'demo': [],
    'assets': {
        'point_of_sale.assets': [
            'q_pdv_orders_repair/static/src/js/models.js',
            'q_pdv_orders_repair/static/src/js/SaleOrderManagementScreen.js',
            'q_pdv_orders_repair/static/src/js/SaleOrderFetcher.js',
            'q_pdv_orders_repair/static/src/js/Orderline.js',
            'q_pdv_orders_repair/static/src/js/SaleOrderRow.js',
            'q_pdv_orders_repair/static/src/js/ProductItem.js',
        ],
        'web.assets_qweb': [
            'q_pdv_orders_repair/static/src/xml/*.xml'
        ],
    },
    'maintainers': [
        'gerardomr8'
    ],
    'installable': True,
    'auto_install': False,
}