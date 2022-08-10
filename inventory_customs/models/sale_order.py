# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import logging
_log = logging.getLogger("___name: %s" % __name__)


class SaleOrderIc(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        self = self.with_context(ic_sale_id=self.id)
        res = super(SaleOrderIc, self).action_confirm()
        return res


class SaleOrderLinePev(models.Model):
    _inherit = "sale.order.line"

    lot_domain_ids = fields.Many2many('stock.production.lot', string="Dominio lot_id", compute="_compute_lot_id_domain", store=False)
    lot_id = fields.Many2one('stock.production.lot', string="#Serie", tracking=True)
    original_price_unit = fields.Float(string="Precio unitario original")
    original_name_line = fields.Char(string="Nombre de linea original")

    @api.onchange('product_id')
    def _compute_lot_id_domain(self):
        for line in self:
            if line.product_uom_qty != 1:
                line.lot_domain_ids = False
                return
            order_location = line.order_id.warehouse_id.lot_stock_id
            # Obtenemos el quant
            quant_domain = [('location_id', '=', order_location.id),
                            ('product_id', '=', line.product_id.id),
                            ('quantity', '>', 0)]
            quant_ids = self.env['stock.quant'].search(quant_domain)
            if not quant_ids:
                line.lot_domain_ids = [(6, 0,[])]
                return
            available_lots = quant_ids.mapped('lot_id')
            if not available_lots:
                line.lot_domain_ids = [(6, 0,[])]
                return
            line.lot_domain_ids = [(6, 0, available_lots.ids)]

    @api.onchange('lot_id')
    def calc_add_costs(self):
        _log.info("Calculando costos adicionales")
        if not self.lot_id:
            self.name = self.original_name_line
            self.price_unit = self.original_price_unit
            return
        if not self.original_price_unit:
            self.original_price_unit = self.price_unit
        if not self.original_name_line:
            self.original_name_line = self.name
        self.name = "%s \n%s" % (self.original_name_line, self.lot_id.tt_free_optional)
        # self.write({
        #     'price_unit': self.original_price_unit + self.lot_id.tt_adc_costs
        # })
        self.price_unit = self.original_price_unit + self.lot_id.tt_adc_costs
