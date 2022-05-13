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
        pos_method_id = None
        amount = 0
        for pay in values.get('payments', []):
            if pay.get('method', {}).get('type') != 'pay_later':
                pos_method_id = pay.get('method', {}).get('id')
                amount = pay.get('amount')
        invoice = values.get('invoice')

        pos_method = self.env['pos.payment.method'].browse(pos_method_id)
        _log.info(pos_method)
        _log.info(pos_method.journal_id)

        journal = pos_method.journal_id
        _log.info("Obtuvo Journal")

        metodos = self.env['account.payment.method.line'].search([('payment_type', '=', 'inbound')], limit=1)
        
        _log.info(metodos)

        _log.info(customer)
        _log.info(journal.id)
        _log.info("Metodos ids")
        _log.info(metodos.id)

        try:
            payment_id = self.create({
                "partner_id" : customer.get('id'),
                "date" : datetime.now().strftime("%Y-%m-%d"),
                "journal_id" : journal.id,
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
            _log.info(payment_id.move_id.id)
            _log.info(payment_id.line_ids)

            for line in payment_id.line_ids:
                _log.info(line.name)
                _log.info(line.account_id.name)
                _log.info(line.debit)
                _log.info(line.credit)

            if payment_id:
                invoice_id = invoice.get('id')
                factura = self.env['account.move'].browse(invoice_id)
                _log.info(factura)
                # factura.payment_id = payment_id


