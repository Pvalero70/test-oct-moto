# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


class PaymentMethodPos(models.Model):
    _inherit = "pos.payment.method"

    payment_method_c = fields.Many2one('l10n_mx_edi.payment.method', string="Forma de pago")


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _order_fields(self, ui_order):
        _log.info(" UI ORDER ==========>>> %s" % ui_order)
        vals = super()._order_fields(ui_order)
        _log.info("1 ========= VALS pos order .. ::: %s " % vals)
        vals['l10n_mx_edi_usage'] = ui_order.get('cfdi_usage')
        _log.info("2 ========= VALS pos order .. ::: %s " % vals)
        # vals['to_invoice'] = True if ui_order.get('to_invoice') else False
        return vals