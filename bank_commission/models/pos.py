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
