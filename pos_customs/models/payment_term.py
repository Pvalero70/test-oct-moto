# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


class PaymentTermUi(models.Model):
    _inherit = "account.payment.term"

    @api.model
    def get_all_terms(self):
        result = self.env['account.payment.term'].sudo().search([])
        if result:
            fres = []
            for res in result:
                te = [res.id, res.name, False]
                fres.append(te)
            return fres
        else:
            return False
