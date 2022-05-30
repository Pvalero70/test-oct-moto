# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_is_zero

class PosOrderLineInherit(models.Model):
    _inherit = 'pos.order.line'

    def _order_line_fields(self, line, session_id):
        result = super()._order_line_fields(line, session_id)
        return result