# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning
from lxml import etree

_logger = logging.getLogger(__name__)


class PurchaseOrderLineDiscount(models.Model):
    _inherit = 'purchase.order.line'

    discount = fields.Float('Descuento %')

    @api.onchange('discount', 'price_unit', 'product_qty')
    def _compute_discount_subtotal(self):
        _logger.info("Descuento computar")
        subtotal = self.price_unit * self.product_qty
        total = subtotal - (subtotal * (self.discount / 100))
        _logger.info("total %s", total)
        self.write({'price_subtotal': total})
