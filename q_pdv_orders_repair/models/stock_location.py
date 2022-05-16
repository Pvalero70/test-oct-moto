# -*- coding: utf-8 -*-
# Copyright 2022 - QUADIT, SA DE CV(https://www.quadit.mx)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _

class StockLocationInherit(models.Model):
    _inherit = "stock.location"

    repair_location = fields.Boolean('It is a repair location?')
    
