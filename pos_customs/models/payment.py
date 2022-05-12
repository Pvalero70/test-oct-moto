# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
import logging
_log = logging.getLogger("___name: %s" % __name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.model_create_multi
    def create(self, vals):
        _log.info("## Intenta crear pago ##")
        _log.info(vals)
        return super(AccountPayment, self).create(vals)

    @api.model
    def crear_pago_pos(self, values):
        _log.info("## Intenta crear pago from pos##")
        _log.info(values)
        values = values.get('vals', {})
        customer = values.get('customer')
        journal_id = None
        amount = 0
        for pay in values.get('payments', []):
            if pay.get('method', {}).get('type') != 'pay_later':
                journal_id = pay.get('method', {}).get('id')
                amount = pay.get('amount')
        invoice = values.get('invoice')

        payment_id = self.create({
            "patner_id" : customer.get('id'),
            "date" : datetime.now().strftime("%Y-%m-%d"),
            "journal_id" : journal_id,
            "amount" : amount,
            "ref" : invoice.get('name')
        })

        if payment_id:
            invoice_id = invoice.get('id')
            factura = self.env['account.move'].browse(invoice_id)
            factura.payment_id = payment_id


