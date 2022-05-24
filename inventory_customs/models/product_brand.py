# -*- coding: utf-8 -*-
from odoo import models, fields, api


class BrandProduct(models.Model):
    _name = 'product.brand'
    _description = "Model that saves the product brand records"

    name = fields.Char()
    brand_image = fields.Binary()
    member_ids = fields.One2many('product.template', 'brand_id')