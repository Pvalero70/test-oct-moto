# -*- coding: utf-8 -*-
# Copyright 2022 - QUADIT, SA DE CV(https://www.quadit.mx)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class RepairOrderInherit(models.Model):
    _inherit = 'repair.order'

    incoming_picking_count = fields.Integer("Incoming Shipment count", compute='_compute_incoming_picking_count')
    picking_ids = fields.Many2many('stock.picking', compute='_compute_picking_ids', string='Receptions', copy=False)
    operation_id = fields.Many2one('stock.picking.type', 'Operation Type', required=True)
    repair_confirm = fields.Boolean('Repair confirm', default=False, copy=False)
    picking_confirm = fields.Boolean('Picking confirm', default=False, copy=False)
    invisible_button = fields.Boolean('Invisible button', copy=False, compute="_invisible_button")

    def _invisible_button(self):
        for record in self:
            if record.repair_confirm or record.picking_confirm:
                if record.repair_confirm and record.picking_confirm:
                    record.invisible_button = False
                else:
                    record.invisible_button = True
            else:
                record.invisible_button = False

    def action_validate(self):
        res = super(RepairOrderInherit, self).action_validate()
        self.repair_confirm = True
        return res
    
    @api.onchange('location_id')
    def _dominios(self):
        for record in self:
            b ={'domain': {'operation_id': [('default_location_dest_id', '=', record.location_id.id),('code', '=', 'incoming')]}}
            return b
    
    def _compute_picking_ids(self):
        for order in self:
            pick_ids = self.env['stock.picking'].search([('origin', '=', order.name)]).ids
            order.picking_ids = pick_ids
    
    def _compute_incoming_picking_count(self):
        for order in self:
            count_incomings = self.env['stock.picking'].search([('origin', '=', order.name)]).ids
            order.incoming_picking_count = len(count_incomings)

    def action_view_picking(self):
        return self._get_action_view_picking(self.picking_ids)

    def action_incoming(self):
        for record in self:
            if not record.partner_id:
                raise ValidationError(_("It is necessary to fill the field 'partner_id' "))
            if not record.location_id:
                raise ValidationError(_("It is necessary to fill the field 'location_id' "))
            if not record.operations:
                raise ValidationError(_("It is necessary to fill the field 'operations' "))
            if not record.operation_id:
                raise ValidationError(_("It is necessary to fill the field 'operation_id' "))
            
            lines_vals = []
            location = self.env['stock.warehouse'].search([('code', '=', record.location_id.location_id.name)])
            obj_picking = self.env['stock.picking']
            record_stock = obj_picking.create(
                {
                    'picking_type_id': record.operation_id.id,
                    'location_id': self.env.ref('stock.stock_location_suppliers').id or False ,
                    'location_dest_id': location.lot_stock_id.id,
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
                'location_id': self.env.ref('stock.stock_location_suppliers').id or False,
                'location_dest_id': location.lot_stock_id.id,
                'lot_ids': [record.lot_id.id],
                })]

            record_stock.sudo().write({'move_ids_without_package': lines_vals})
            record_stock.action_confirm()            


    def _get_action_view_picking(self, pickings):
        """ This function returns an action that display existing picking orders of given purchase order ids. When only one found, show the picking immediately.
        """
        self.ensure_one()
        print(pickings)
        result = self.env["ir.actions.actions"]._for_xml_id('stock.action_picking_tree_all')
        result['context'] = {'origin': self.name}
        if not pickings or len(pickings) > 1:
            result['domain'] = [('id', 'in', pickings.ids)]
        elif len(pickings) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            form_view = [(res and res.id or False, 'form')]
            result['views'] = form_view + [(state, view) for state, view in result.get('views', []) if view != 'form']
            result['res_id'] = pickings.id
        return result