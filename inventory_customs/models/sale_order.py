# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import logging
_log = logging.getLogger("___name: %s" % __name__)


class SaleOrderLinePev(models.Model):
    _inherit = "sale.order.line"

    lot_id = fields.Many2one('stock.production.lot')
    