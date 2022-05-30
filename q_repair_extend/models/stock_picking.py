# -*- coding: utf-8 -*-
# Copyright 2022 - QUADIT, SA DE CV(https://www.quadit.mx)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _

class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super(StockPickingInherit, self).button_validate()
        record_repair = self.env['repair.order'].search([('name','=',self.origin)])
        print(record_repair)
        if record_repair:
            record_repair.write({'picking_confirm': True})
        return res