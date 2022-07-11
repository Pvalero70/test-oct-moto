# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import pytz
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
    bc_journal_id = fields.Many2one("account.journal", string="Diario de comisiones")
    product_cate_commission_ids = fields.Many2many('product.category', string="Categorías de producto para comisión")


class PosPaymentBc(models.Model):
    _inherit = "pos.payment.method"

    is_commission = fields.Boolean(string="Es pago de comision", default=False)

