# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import logging
_log = logging.getLogger("___name: %s" % __name__)


class SaleOrderLinePev(models.Model):
    _inherit = "sale.order.line"

    lot_domain_ids = fields.Many2many('stock.production.lot', string="Dominio lot_id", compute="_compute_lot_id_domain", store=False)
    lot_id = fields.Many2one('stock.production.lot', string="#Serie")

    def _compute_lot_id_domain(self):
        if self.product_uom_qty != 1:
            self.lot_domain_ids = False
            return
        order_location = self.order_id.warehouse_id.lot_stock_id
        # Obtenemos el quant
        quant_domain = [('location_id', '=', order_location.id),
                        ('product_id', '=', self.product_id.id),
                        ('quantity', '>', 0)]
        quant_ids = self.env['stock.quant'].search(quant_domain)
        available_lots = quant_ids.mapped('lot_id')
        if not available_lots:
            return
        self.lot_domain_ids = [(6, 0, available_lots.ids)]
