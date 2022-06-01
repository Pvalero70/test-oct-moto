# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning
from lxml import etree


_logger = logging.getLogger(__name__)


class PurchaseOrderLineDiscount(models.Model):
    _inherit = 'purchase.order.line'

    discount = fields.Integer('Descuento %')
