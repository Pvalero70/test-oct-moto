# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


class ProductCategoryCus(models.Model):
    _inherit = "product.category"

    target_journal_id = fields.Many2one('account.journal', "Diario afectado")