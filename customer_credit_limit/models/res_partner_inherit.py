# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ResPartnerCreditLimit(models.Model):
    _inherit = "res.partner"
    _sql_constraints = [
        ('customer_internal_ref', 'unique (ref)', 'La referencia interna del cliente debe ser única.')
    ]

    credit_limit = fields.Monetary(string="Limite de crédito", default=0.00)
    active_credit_limit = fields.Boolean(string="Limite de crédito")

    @api.constrains('credit_limit')
    def _check_credit_amount(self):
        for credit in self:
            if credit.credit_limit > 0 and credit.active_credit_limit:
                raise ValidationError(_('Advertencia!, el limite de crédito debe ser mayor a cero.'))

