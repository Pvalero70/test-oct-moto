# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


class AccountJournalC(models.Model):
    _inherit = "account.journal"

    c_product_category_id = fields.Many2one('product.category', string="Categoría de productos")
    c_location_id = fields.Many2one('stock.location')


