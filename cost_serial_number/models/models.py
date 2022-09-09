# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

from datetime import datetime
from odoo.tools import float_is_zero, OrderedSet

import logging

_logger = logging.getLogger(__name__)

class StockMove(models.Model):
	_inherit = 'stock.move'

	def _create_out_svl(self, forced_quantity=None):
		"""Create a `stock.valuation.layer` from `self`.

		:param forced_quantity: under some circunstances, the quantity to value is different than
			the initial demand of the move (Default value = None)
		"""
		_logger.info("## Override create out svl module ##")
		svl_vals_list = []
		for move in self:
			move = move.with_company(move.company_id)
			valued_move_lines = move._get_out_move_lines()
			valued_quantity = 0
			for valued_move_line in valued_move_lines:
				_logger.info("## valued move line")
				_logger.info(valued_move_line)
				_logger.info(valued_move_line.lot_id)
				valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)
			if float_is_zero(forced_quantity or valued_quantity, precision_rounding=move.product_id.uom_id.rounding):
				continue
			svl_vals = move.product_id._prepare_out_svl_vals(forced_quantity or valued_quantity, move.company_id)
			svl_vals.update(move._prepare_common_svl_vals())
			if forced_quantity:
				svl_vals['description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name
			svl_vals['description'] += svl_vals.pop('rounding_adjustment', '')
			svl_vals_list.append(svl_vals)
		return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

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
					for line in move_line:
						_logger.info("Se obtuvo la linea del movimiento")
						move = move_line.move_id
						if move.purchase_line_id:
							_logger.info("Se obtuvo el precio unitario de la compra")
							price_unit = move.purchase_line_id.price_unit
							line.purchase_price = price_unit
							return

			line.purchase_price = 50

