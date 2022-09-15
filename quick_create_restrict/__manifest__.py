# -*- coding: utf-8 -*-

# Copyright © 2018 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (<support@garazd.biz>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    'name': 'Restricciones Creado Rapido Odoo 15',
    'version': '15.0.1.0.1',
    'category': 'sale',
    'author': 'Ing. Alejandro Garcia Magaña',
    'website': '',
    'license': 'LGPL-3',
    'summary': 'Restricciones de creado rapido en Compras, Ventas, Inventario, Partners ',

    'depends': [
        'repair',
        'sale_management',
        'sale',
        'sale_stock',
        'base',
        'account',
        'stock',
        'stock_landed_costs',
        'product',
        'purchase',
    ],
    'data': [
        'views/quick_create_sale.xml',
        'views/quick_create_partner.xml',
        'views/quick_create_product.xml',
        'views/quick_create_category.xml',
        'views/quick_create_repair.xml',
        'views/quick_create_purchase.xml',
        'views/quick_create_account.xml',
        'views/quick_create_inventory.xml',
    ],
    'demo': [],
    'external_dependencies': {
    },
    'support': 'support@garazd.biz',
    'application': False,
    'installable': True,
    'auto_install': False,
}
