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
    ])

    # Marca, Número de motor, Modelo, Color, Cilindros y Desplazamiento. Cuando un producto sea refacción, accesorio u otro, deberá de llevar el campo de Marca

    brand_id = fields.Many2one('product.brand', string='Marca')

