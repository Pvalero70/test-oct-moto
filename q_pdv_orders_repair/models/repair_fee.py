# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_is_zero

class PosOrderInherit(models.Model):
    _inherit = "repair.fee"
    _description = "Repair fees"

    def read_converted(self):
        user_admin = self.env.ref('base.user_admin')
        field_names = ["product_id", "name", "price_unit", "product_uom_qty", "tax_id", "price_total"]
        results = []
        for sale_line in self:
            if sale_line:
                product_uom = sale_line.product_id.uom_id
                sale_line_uom = sale_line.product_uom
                item = sale_line.with_user(user_admin).read(field_names)[0]
                if sale_line.product_id.tracking != 'none':
                    item['lot_names'] = sale_line.move_ids.move_line_ids.lot_id.mapped('name')
                if product_uom == sale_line_uom:
                    results.append(item)
                    continue
                item['product_uom_qty'] = self._convert_qty(sale_line, item['product_uom_qty'], 's2p')
                item['qty_delivered'] = 0
                item['qty_invoiced'] = 0
                item['qty_to_invoice'] = 0
                item['price_unit'] = sale_line_uom._compute_price(item['price_unit'], product_uom)
                results.append(item)
        return results