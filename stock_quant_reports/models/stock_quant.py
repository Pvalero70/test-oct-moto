# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning
from lxml import etree

_logger = logging.getLogger(__name__)


class PurchaseOrderLineDiscount(models.Model):
    _inherit = 'stock.quant'

    default_code = fields.Char(string="Referencia interna", related='product_id.default_code')

