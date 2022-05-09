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
            _log.info("\n Factura a revisar::: (%s) $s " % inv.name, inv)
            if not inv.pos_order_ids:
                continue
            _log.info("\n Factura del punto de venta")
            invoice_pos_payment_methods = inv.pos_order_ids.mapped('payment_method_id').filtered(lambda bcm: bcm.bank_commission_method != False)
            if not invoice_pos_payment_methods:
                continue
            self.create_bc_inv(inv)
        return invoices

    @api.model
    def create_bc_inv(self, inv):
        _log.info("\n Creando comisión para la factura:: %s " % inv)