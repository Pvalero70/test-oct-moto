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

        journal = self.env['account.journal'].browse(journal_id)
        metodos = self.env['account.payment.method.line'].search([('payment_type', '=', 'inbound')], limit=1)
        
        _log.info(metodos)

        try:
            payment_id = self.create({
                "partner_id" : customer.get('id'),
                "date" : datetime.now().strftime("%Y-%m-%d"),
                "journal_id" : journal_id,
                "payment_method_line_id" : metodos.id,
                "amount" : amount,
                "payment_type" : "inbound",
                "ref" : invoice.get('name')
            })
        except Exception as e:
            _log.error(e)
        else:
            _log.info("Pago creado")
            _log.info(payment_id)

            if payment_id:
                invoice_id = invoice.get('id')
                factura = self.env['account.move'].browse(invoice_id)
                _log.info(factura)
                factura.payment_id = payment_id


