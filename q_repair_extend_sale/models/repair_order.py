# -*- coding: utf-8 -*-
# Copyright 2022 - QUADIT, SA DE CV(https://www.quadit.mx)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class RepairOrderInherit(models.Model):
    _inherit = 'repair.order'

    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_sale_count', copy=False)
    picking_sale_ids = fields.Many2many('stock.picking', compute='_compute_picking_sale_ids', string='Receptions', copy=False)
    picking_sale_confirm = fields.Boolean('Picking sale confirm', default=False, copy=False)
    location_id = fields.Many2one('stock.location', 'Location', index=True, readonly=True, required=True, check_company=True,
                                  help="This is the location where the product to repair is located.",
                                  default=lambda self: self.env.user.property_warehouse_id.lot_stock_id,
                                  states={'draft': [('readonly', False)], 'confirmed': [('readonly', True)]}, domain="[('usage', '=', 'internal')]")
    invoice_method = fields.Selection([
        ("none", "No Invoice"),
        ("b4repair", "Before Repair"),
        ("after_repair", "After Repair")], string="Invoice Method",
        default='after_repair', index=True, readonly=True, required=True,
        states={'draft': [('readonly', False)]},
        help='Selecting \'Before Repair\' or \'After Repair\' will allow you to generate invoice before or after the repair is done respectively. \'No invoice\' means you don\'t want to generate invoice for this repair order.')

    def _compute_picking_sale_count(self):
         for order in self:
            pick_ids = self.env['stock.picking'].search([('origin', '=', order.name), ('picking_type_code', '=', 'outgoing')]).ids
            order.delivery_count = len(pick_ids)

    def _compute_picking_sale_ids(self):
         for order in self:
            pick_ids = self.env['stock.picking'].search([('origin', '=', order.name), ('picking_type_code', '=', 'outgoing')]).ids
            order.picking_sale_ids = pick_ids

    def action_view_delivery(self):
        return self._get_action_view_picking(self.picking_sale_ids)

    def action_out_sale(self):
        for record in self:
            print("Vamos a crear la orden de salida")
            location = self.env['stock.warehouse'].search([('code', '=', record.location_id.location_id.name)])
            obj_picking = self.env['stock.picking']
            record_stock = obj_picking.create(
                {
                    'picking_type_code': 'outgoing',
                    'partner_id': record.partner_id.id,
                    'picking_type_id': location.out_type_id.id,
                    'location_id': location.lot_stock_id.id,
                    'location_dest_id': self.env.ref('stock.stock_location_customers').id or False,
                    'scheduled_date': record.schedule_date,
                    'origin': record.name,
                    'owner_id': record.partner_id.id,
                }
            )

            lines_vals =  [(0, 0,{
                'name': record.product_id.name,
                'product_id': record.product_id.id,
                'product_uom_qty': record.product_qty,
                'product_uom':record.product_uom.id,
                'description_picking': record.product_id.name,
                'picking_id': record_stock.id,
                'location_id': location.lot_stock_id.id,
                'location_dest_id': self.env.ref('stock.stock_location_customers').id or False,
                'lot_ids': [record.lot_id.id],
                })]

            record_stock.sudo().write({'move_ids_without_package': lines_vals})
            record_stock.action_confirm()   
            record.write({'picking_sale_confirm': True})