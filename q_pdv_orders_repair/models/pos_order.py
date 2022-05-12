# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_is_zero
from functools import partial


class PosOrderInherit(models.Model):
    _inherit = "pos.order"
    _description = "Point of Sale Orders"

    ref_repair = fields.Integer("Repair reference")

    @api.model
    def _order_fields(self, ui_order):
        process_line = partial(self.env['pos.order.line']._order_line_fields, session_id=ui_order['pos_session_id'])
        
        return {
            'user_id': ui_order['user_id'] or False,
            'session_id': ui_order['pos_session_id'],
            'lines': [process_line(l) for l in ui_order['lines']] if ui_order['lines'] else False,
            'pos_reference': ui_order['name'],
            'sequence_number': ui_order['sequence_number'],
            'partner_id': ui_order['partner_id'] or False,
            'date_order': ui_order['creation_date'].replace('T', ' ')[:19],
            'fiscal_position_id': ui_order['fiscal_position_id'],
            'pricelist_id': ui_order['pricelist_id'],
            'amount_paid':  ui_order['amount_paid'],
            'amount_total': ui_order['amount_total'],
            'amount_tax':  ui_order['amount_tax'],
            'amount_return': ui_order['amount_return'],
            'company_id': self.env['pos.session'].browse(ui_order['pos_session_id']).company_id.id,
            'to_invoice': ui_order['to_invoice'] if "to_invoice" in ui_order else False,
            'to_ship': ui_order['to_ship'] if "to_ship" in ui_order else False,
            'is_tipped': ui_order.get('is_tipped', False),
            'tip_amount': ui_order.get('tip_amount', 0),
            'ref_repair': ui_order.get('ref_repair', False),
        }
    
    @api.model
    def create(self, values):
        session = self.env['pos.session'].browse(values['session_id'])
        values = self._complete_values_from_session(session, values)
        return super(PosOrderInherit, self).create(values)

    @api.model
    def _process_order(self, order, draft, existing_order):
        res = super(PosOrderInherit, self)._process_order(order, draft, existing_order)
        order = order['data']
        if 'ref_repair' in order:
            if order['to_invoice'] and order['ref_repair']:
                repair = self.env['repair.order'].search([('id', '=', order['ref_repair'])])
                if repair:
                    repair.action_repair_invoice_create()
        return res