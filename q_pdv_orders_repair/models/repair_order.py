# -*- coding: utf-8 -*-
# Copyright 2022 - QUADIT, SA DE CV(https://www.quadit.mx)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import logging


_log = logging.getLogger("___name: %s" % __name__)

class RepairOrderInherit(models.Model):
    _inherit = 'repair.order'

    tpv_count = fields.Integer(string='Pos Orders', compute='_compute_tpv_count', copy=False)
    tpv_ids = fields.Many2many('pos.order', compute='_compute_tpv_ids', string='Pos Orders', copy=False)
    is_ready_to_pos = fields.Boolean(string="Esta todo correcto para pasarla al pos",compute="_computed_is_ready",store=True)

    def _computed_is_ready(self):
        for rec in self:

            rec._compute_fees_lines_ok()
            _log.info("COMPUTAMOS %s , disponible pos %s", rec.name, rec.is_ready_to_pos)

    @api.depends('fees_lines', 'fees_lines.sale_ok', 'fees_lines.available_in_pos')
    def _compute_fees_lines_ok(self):
        _log.info("Ha cambiado una fee_line %s , disponible pos %s %s", self.name, self.sale_ok,self.available_in_pos)
        for fee in self.fees_lines:
            if fee.product_id and fee.product_id.sale_ok and fee.product_id.available_in_pos:
                continue
            else:
                self.is_ready_to_pos = False
                _log.info("Ha cambiado una fee_line to false %s , disponible pos %s ", self.name, self.is_ready_to_pos)
                return

        self.is_ready_to_pos = True
        _log.info("Ha cambiado una fee_line to true %s , disponible pos %s ", self.name, self.is_ready_to_pos)

    def _compute_tpv_count(self):
         for order in self:
            orders_ids = self.env['pos.order'].search([('ref_repair','=', self.id)]).ids
            order.tpv_count = len(orders_ids)

    def _compute_tpv_ids(self):
         for order in self:
            orders_ids = self.env['pos.order'].search([('ref_repair','=', self.id)]).ids
            order.tpv_ids = orders_ids
    
    def action_pos_view(self):
        return self.action_view_pos_order(self.tpv_ids)

    def action_view_pos_order(self, order):
        self.ensure_one()
        linked_orders = order.ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Linked POS Orders'),
            'res_model': 'pos.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', linked_orders)],
        }