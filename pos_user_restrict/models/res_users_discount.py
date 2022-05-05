# -*- coding: utf-8 -*-

from odoo import fields, models

class ResUserInheritDiscount(models.Model):
    _inherit = 'res.users'

    discount_ids = fields.One2many('res.users.discount','seller_id',String="Lista de Descuentos")


class ResUsersDiscount(models.Model):
    _name = 'res.users.discount'

    _description = "Model that saves discounts on product categories"

    seller_id = fields.Many2one('res.users' , 'Vendedor')
    discount_permitted = fields.Integer('Descuento permitido')
    category_ids = fields.Many2many('product.category' , 'Categorias')

