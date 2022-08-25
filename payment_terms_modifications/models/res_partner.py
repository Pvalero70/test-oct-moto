import logging
from collections import defaultdict

from odoo import _, api, Command, fields, models
from lxml import etree
from odoo.exceptions import ValidationError, UserError, Warning

_logger = logging.getLogger(__name__)


class ResPartnerPaymentPerm(models.Model):
    _inherit = 'res.partner'


    payment_terms_permission = fields.Boolean(string="Readonly para el campo terminos de pago", readonly=False,
                                        compute='get_user_payment_term')

    @api.onchange('first_name', 'second_name', 'first_ap', 'second_ap')
    @api.depends('payment_terms_permission')
    def get_user_payment_term(self):
        res_user = self.env.user
        if res_user.has_group('payment_terms_modifications.payment_term_readonly_group'):
            self.payment_terms_permission = True
        else:
            self.payment_terms_permission = False


