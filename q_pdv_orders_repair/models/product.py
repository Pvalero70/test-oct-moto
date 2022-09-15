# -*- coding: utf-8 -*-
# Copyright 2022 - QUADIT, SA DE CV(https://www.quadit.mx)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import logging

_log = logging.getLogger("___name: %s" % __name__)


class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    def write(self, values):
        res = super(ProductProductInherit, self).write(values)
        if 'sale_ok' in values or 'available_in_pos' in values:
            repair_orders = self.env['repair.order'].search([('state', '=', '2binvoiced')])
            for repair in repair_orders:
                repair.compute_fees_lines_ok()

        return res

