# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

from datetime import datetime

import logging

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

	@api.depends('move_ids', 'move_ids.stock_valuation_layer_ids', 'order_id.picking_ids.state')
	def _compute_purchase_price(self):
		_logger.info("### OVERRIDE PURCHASE PRICE ###")
		for line in self:
			line.purchase_price = 50

