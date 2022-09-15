# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    restrict_locations = fields.Boolean('Restrict Location')

    stock_location_ids = fields.Many2many(
        'stock.location',
        'location_security_stock_location_users',
        'user_id',
        'location_id',
        'Ubicaciones de existencias')

    default_picking_type_ids = fields.Many2many(
        'stock.picking.type', 'stock_picking_type_users_rel',
        'user_id', 'picking_type_id', string='Operaciones de almacén predeterminadas')


class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.constrains('state', 'location_id', 'location_dest_id')
    def check_user_location_rights(self):
        for rec in self:
            if rec.state == 'draft':
                return True

            user_locations = []
            for i in rec.env.user.stock_location_ids:
                user_locations.append(i.id)

            # user_locations = rec.env.user.stock_location_ids
            if rec.env.user.restrict_locations:
                message = _(
                    'Invalid Location. You cannot process this move since you do '
                    'not control the location "%s". '
                    'Please contact your Administrator.')

                if rec.location_id.id not in user_locations:
                    raise UserError(message % rec.location_id.name)
                elif rec.location_dest_id.id not in user_locations:
                    raise UserError(message % rec.location_dest_id.name)



class stockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.onchange('product_id', 'company_id')
    def _onchange_product_id(self):
        if self.location_id:
            return
        if self.product_id.tracking in ['lot', 'serial']:
            previous_quants = self.env['stock.quant'].search([
                ('product_id', '=', self.product_id.id),
                ('location_id.usage', 'in', ['internal', 'transit'])], limit=1, order='create_date desc')
            if previous_quants:
                self.location_id = previous_quants.location_id
        if not self.location_id:
            company_id = self.company_id and self.company_id.id or self.env.company.id
            if self.env.user.has_group('warehouse_stock_restrictions.group_restrict_warehouse'):
                picking_types = [elem.id for elem in self.env.user.default_picking_type_ids]
                type_id = self.env['stock.picking.type'].search(
                    [('company_id', '=', company_id),('id','in',picking_types),('default_location_dest_id','!=',None)], limit=1)
                if type_id:
                    self.location_id = type_id.default_location_dest_id
            else:
                self.location_id = self.env['stock.warehouse'].search(
                    [('company_id', '=', company_id)],
                    limit=1).in_type_id.default_location_dest_id



