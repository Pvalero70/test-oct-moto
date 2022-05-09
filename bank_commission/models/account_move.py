# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import logging
_log = logging.getLogger("___name: %s" % __name__)


class AccountMoveBc(models.Model):
    _inherit = "account.move"

    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        invoices = super(AccountMoveBc, self).create(vals_list)
        for inv in invoices:
            _log.info("\n Factura a revisar::: (%s) $s " % (inv.name, inv))
        return invoices

