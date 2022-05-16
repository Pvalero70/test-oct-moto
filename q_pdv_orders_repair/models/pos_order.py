# -*- coding: utf-8 -*-
# Copyright 2022 - QUADIT, SA DE CV(https://www.quadit.mx)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_is_zero
from functools import partial
from odoo.exceptions import ValidationError

class PosOrderInherit(models.Model):
    _inherit = "pos.order"
    _description = "Point of Sale Orders"

    ref_repair = fields.Integer("Repair reference")
    repair_count = fields.Integer(string='Orders repair count', compute='_compute_repair_count', copy=False)
    repair_ids = fields.Many2many('repair.order', compute='_compute_repair_ids', string='Orders Repair', copy=False)

    @api.model
    def _order_fields(self, ui_order):
        
        if 'ref_repair' in ui_order:
            process_line = partial(self.env['pos.order.line']._order_line_fields_repair, session_id=ui_order['pos_session_id'])
        else:
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

    def _create_order_picking(self):
        self.ensure_one()
        if not self.ref_repair:
            res = super(PosOrderInherit, self)._create_order_picking()
        else:
            if self.to_ship:
                self.lines._launch_stock_rule_from_pos_order_lines()
            else:
                if self._should_create_picking_real_time():
                    picking_type = self.config_id.picking_type_id
                    destination_id = picking_type.default_location_repair_id.id
                    if destination_id:
                        pickings = self.env['stock.picking']._create_picking_from_pos_order_lines(destination_id, self.lines, picking_type, self.partner_id)
                        pickings.write({'pos_session_id': self.session_id.id, 'pos_order_id': self.id, 'origin': self.name})
                    else:
                        raise ValidationError(_("If you are creating a repair it is necessary to add a repair location in the configuration."))

    def _compute_repair_count(self):
         for order in self:
            if order.ref_repair:
                orders_ids = self.env['repair.order'].search([('id','=', order.ref_repair)]).ids
                order.repair_count = len(orders_ids)
            else:
                order.repair_count = 0

    def _compute_repair_ids(self):
         for order in self:
            if order.ref_repair:
                orders_ids = self.env['repair.order'].search([('id','=', order.ref_repair)]).ids
                order.repair_ids = orders_ids
            else:
                order.repair_ids = 0
    
    def action_repair_view(self):
        for order in self:
            return self.action_view_repair_order(order.repair_ids)

    def action_view_repair_order(self, order):
        self.ensure_one()
        linked_orders = order.ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Linked Repair Orders'),
            'res_model': 'repair.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', linked_orders)],
        }

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    def _order_line_fields_repair(self, line, session_id):
        line[2]['sale_order_origin_id'] = False
        result = super()._order_line_fields(line, session_id)
        return result