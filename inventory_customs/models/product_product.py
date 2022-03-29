# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


class ProductTemplateCus(models.Model):
    _inherit = "product.template"

    product_inv_categ = fields.Selection([
        ('moto', 'Motocicleta'),
        ('refaccion', 'Refacción'),
        ('accesorio', 'Accesorio'),
        ('servicio', 'Servicio')
    ], string="Categoria de producto")