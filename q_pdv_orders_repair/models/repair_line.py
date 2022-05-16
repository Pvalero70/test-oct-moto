# -*- coding: utf-8 -*-
# Copyright 2022 - QUADIT, SA DE CV(https://www.quadit.mx)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_is_zero

class PosOrderInherit(models.Model):
    _inherit = "repair.line"
    _description = "Repair lines"

    def read_converted(self):
        user_admin = self.env.ref('base.user_admin')
        field_names = ["product_id", "name", "price_unit", "product_uom_qty", "tax_id", "price_total", "lot_id"]
        results = []
        for repair_line in self:
            if repair_line:
                product_uom = repair_line.product_id.uom_id
                repair_line_uom = repair_line.product_uom
                item = repair_line.with_user(user_admin).read(field_names)[0]
                if repair_line.product_id.tracking != 'none':
                    item['lot_names'] = repair_line.lot_id.mapped('name')
                if product_uom == repair_line_uom:
                    results.append(item)
                    continue
                item['product_uom_qty'] = self._convert_qty(repair_line, item['product_uom_qty'], 's2p')
                item['qty_delivered'] = 0
                item['qty_invoiced'] = 0
                item['qty_to_invoice'] = 0
                item['price_unit'] = repair_line_uom._compute_price(item['price_unit'], product_uom)
                results.append(item)
        return results