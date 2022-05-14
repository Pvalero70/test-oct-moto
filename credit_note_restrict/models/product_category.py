# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning

_logger = logging.getLogger(__name__)


class ResUserInheritDiscount(models.Model):
    _inherit = 'product.category'

    account_credit_note_id = fields.Many2one('account.account',"Cuenta de nota de credito")
    account_discount_id = fields.Many2one('account.account', "Cuenta de descuento o devolucion")

