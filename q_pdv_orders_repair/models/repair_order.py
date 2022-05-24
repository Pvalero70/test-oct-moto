# -*- coding: utf-8 -*-
# Copyright 2022 - QUADIT, SA DE CV(https://www.quadit.mx)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class RepairOrderInherit(models.Model):
    _inherit = 'repair.order'

    tpv_count = fields.Integer(string='Pos Orders', compute='_compute_tpv_count', copy=False)
    tpv_ids = fields.Many2many('pos.order', compute='_compute_tpv_ids', string='Pos Orders', copy=False)
    
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