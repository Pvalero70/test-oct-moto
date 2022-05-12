# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.model_create_multi
    def create(self, vals):
        _log.info("## Intenta crear pago ##")
        _log.info(vals)
        return super(AccountPayment, self).create(vals)