# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

from datetime import datetime

import logging

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	@api.onchange("lot_id")
	def _onchange_lot_id(self):
		_logger.info("## CAMBIA LOTE ##")
		self._compute_purchase_price()

	@api.depends('move_ids', 'move_ids.stock_valuation_layer_ids', 'order_id.picking_ids.state')
	def _compute_purchase_price(self):
		_logger.info("### OVERRIDE PURCHASE PRICE ###")
		for line in self:
			
			if line.lot_id:
				move_line = self.env['stock.move.line'].search([('lot_id', '=', line.lot_id.id)])
				if move_line:
					_logger.info("Se obtuvo la linea del movimiento")
					move = move_line.move_id
					if move.purchase_line_id:
						_logger.info("Se obtuvo el precio unitario de la compra")
						price_unit = move.purchase_line_id
						line.purchase_price = price_unit
						return

			line.purchase_price = 50

