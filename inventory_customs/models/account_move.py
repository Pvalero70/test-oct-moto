# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


class AccountMoveItt(models.Model):
    _inherit = "account.move"

    def _get_invoiced_lot_values_tt(self, product_id=None):
        # Poner aquí la restricción de la compañia.
        _log.info("\nCalculando para el producto:: %s" % product_id)
        if self.move_type != "out_invoice" or self.state == 'draft':
            return False
        sale_lines = self.invoice_line_ids.sale_line_ids
        # sale_orders = sale_lines.order_id
        # Filter lines for specific product
        stock_move_lines = sale_lines.move_ids.filtered(lambda r: r.state == 'done').move_line_ids.filtered(lambda r: r.product_id == product_id.id)
        data = []
        for line in stock_move_lines:
            if not line.product_id.product_inv_categ or not line.product_id.product_inv_categ in ["moto", "Moto"]:
                continue
            # Put: color; inv num,
            data.append({
                'serial': line.lot_id.name,
                'motor_num': line.lot_id.tt_motor_number,
                'color': line.lot_id.tt_color,
                'inv_num': line.lot_id.tt_inventory_number,
            })

        if len(data) <= 0:
            return False
        return data
