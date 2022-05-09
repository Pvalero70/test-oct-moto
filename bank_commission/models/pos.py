# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import logging
_log = logging.getLogger("___name: %s" % __name__)


class PosPaymentMethodBc(models.Model):
    _inherit = "pos.payment.method"

    bank_commission_method = fields.Selection([
        ("percentage", "Porcentaje"),
        ("fixed", "Monto fijo")
    ], string="Método de calculo comisión")
    bank_commission_amount = fields.Float(string="Monto de comisión")
    bank_commission_product_id = fields.Many2one('product.product', string="Concepto comisión")


class PosOrderBc(models.Model):
    _inherit = "pos.order"

    def _create_invoice(self,vals):
        res = super(PosOrderBc, self)
        # Creating new invoice for commission bank
        _log.info("\n Creando factura para.. ")
        for payment in self.payment_ids.filtered(lambda x: x.payment_method_id.bank_commission_method is not False):
            self._create_bc_invoice(payment)
        return res

    @api.model
    def _create_bc_invoice(self, payment):
        _log.info("\n Creando factura para el pago:: %s" % payment)
