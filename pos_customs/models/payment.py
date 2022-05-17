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
        # _log.info("## Intenta crear pago from pos##")
        # _log.info(values)
        values = values.get('vals', {})
        customer = values.get('customer')
        pos_method_id = None
        amount = 0
        for pay in values.get('payments', []):
            if pay.get('method', {}).get('type') != 'pay_later':
                pos_method_id = pay.get('method', {}).get('id')
                amount = pay.get('amount')
        invoice = values.get('invoice')
        pos_session_id = invoice.get('pos_session_id')
        # _log.info(pos_session_id)

        pos_method = self.env['pos.payment.method'].browse(pos_method_id)
        # _log.info(pos_method)
        # _log.info(pos_method.journal_id)

        journal = pos_method.journal_id
        forma_pago = pos_method.payment_method_c
        # _log.info("Obtuvo Journal")

        metodos = self.env['account.payment.method.line'].search([('payment_type', '=', 'inbound')], limit=1)
        
        # _log.info(metodos)

        # _log.info(customer)
        # _log.info(journal.id)
        # _log.info("Metodos ids")
        # _log.info(metodos.id)

        # payment_method_id = journal.l10n_mx_edi_payment_method_id.id

        try:
            payment_id = self.create({
                "partner_id" : customer.get('id'),
                "date" : datetime.now().strftime("%Y-%m-%d"),
                "journal_id" : journal.id,
                "payment_method_line_id" : metodos.id,                
                "amount" : amount,
                "pos_session_id" : pos_session_id,
                "payment_type" : "inbound",
                "ref" : invoice.get('name')
            })
        except Exception as e:
            _log.error(e)
        else:
            # _log.info("Pago creado")
            # _log.info(payment_id)
            # _log.info(payment_id.move_id.id)
            # _log.info(payment_id.line_ids)
            
            credit_line_id = None
            for line in payment_id.line_ids:
                # _log.info(line.name)
                # _log.info(line.account_id.name)
                # _log.info(line.debit)
                # _log.info(line.credit)

                if line.credit > 0:
                    credit_line_id = line.id

            if payment_id:

                if forma_pago:
                    payment_id.write({"l10n_mx_edi_payment_method_id" : forma_pago.id})

                payment_id.action_post()
                invoice_id = invoice.get('id')
                factura = self.env['account.move'].browse(invoice_id)
                if credit_line_id:
                    lines = self.env['account.move.line'].browse(credit_line_id)
                    # _log.info("debug")
                    # _log.info(factura.line_ids)
                    # for iline in factura.line_ids:
                    #     _log.info(iline.account_id.id)
                    #     _log.info(iline.account_id.name)
                    #     _log.info(iline.credit)
                    #     _log.info(iline.debit)
                    #     _log.info("#####")
                    # invoice_lines = 
                    invoice_lines = factura.line_ids.filtered(lambda line: line.account_id == lines[0].account_id and not line.reconciled)
                    # _log.info("### invoice lines ###")
                    # _log.info(invoice_lines)
                    
                    if invoice_lines:
                        lines += invoice_lines
                        # _log.info(lines)
                        rec = lines.reconcile()
                        _log.info("Reconciled")
                        _log.info(rec)
                    # else:
                    #     _log.info("Sin invoice lines")
                # _log.info("### Facturas ###")
                # _log.info(factura)
                # factura.payment_id = payment_id


