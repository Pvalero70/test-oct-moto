# -*- coding: utf-8 -*-
# Copyright 2022 - QUADIT, SA DE CV(https://www.quadit.mx)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class RepairLineInherit(models.Model):
    _inherit = 'repair.line'

    location_id = fields.Many2one('stock.location', 'Source Location', index=True, required=True, check_company=True, default=lambda self: self.env.user.property_warehouse_id.lot_stock_id, domain="[('usage', '=', 'internal')]")

    @api.onchange('type')
    def onchange_operation_type(self):
        """ On change of operation type it sets source location, destination location
        and to invoice field.
        @param product: Changed operation type.
        @param guarantee_limit: Guarantee limit of current record.
        @return: Dictionary of values.
        """
        if not self.type:
            self.location_id = False
            self.location_dest_id = False
        elif self.type == 'add':
            self.onchange_product_id()
            args = self.repair_id.company_id and [('company_id', '=', self.repair_id.company_id.id)] or []
            warehouse = self.env['stock.warehouse'].search(args, limit=1)
            self.location_id = self.repair_id.location_id.id
            self.location_dest_id = self.env['stock.location'].search([('usage', '=', 'production'), ('company_id', '=', self.repair_id.company_id.id)], limit=1)
        else:
            self.price_unit = 0.0
            self.tax_id = False
            self.location_id = self.env['stock.location'].search([('usage', '=', 'production'), ('company_id', '=', self.repair_id.company_id.id)], limit=1).id
            self.location_dest_id = self.env['stock.location'].search([('scrap_location', '=', True), ('company_id', 'in', [self.repair_id.company_id.id, False])], limit=1).id