# -*- coding: utf-8 -*-
# Copyright 2022 - QUADIT, SA DE CV(https://www.quadit.mx)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _

class StockPickingTypeInherit(models.Model):
    _inherit = "stock.picking.type"
    
    default_location_repair_id = fields.Many2one('stock.location', string='Default location repair')