# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
import json
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
        values = values.get('vals', {})

        invoice = values.get('invoice')
        # QUITAR PAGOS DE COMISION AQUÍ. (Buscamos la comisión deacuerdo al monto de comisión que tiene el pos order.. )
        ''
        if 'order_lines_data' in values and len(values.get('order_lines_data')) > 0:
            new_payments = []
            pold = values.get('order_lines_data')[0]
            order_line_amount = pold['amount']
            tax_factor = self.env['pos.payment'].get_comm_product_tax(commission_product_id=pold['product_id'])
            line_comm_amount = round(tax_factor*order_line_amount, 2)
            for pay in values.get('payments', []):
                if float(pay['amount']) != line_comm_amount:
                    new_payments.append(pay)
            values['payments'] = new_payments

        customer = values.get('customer')
        pos_method_id = None
        amount = 0
        for pay in values.get('payments', []):
            if pay.get('method', {}).get('type') != 'pay_later':
                pos_method_id = pay.get('method', {}).get('id')
                amount = pay.get('amount')

        pos_session_id = invoice.get('pos_session_id')
        pos_method = self.env['pos.payment.method'].browse(pos_method_id)

        journal = pos_method.journal_id
        forma_pago = pos_method.payment_method_c

        metodos = self.env['account.payment.method.line'].search([('payment_type', '=', 'inbound')], limit=1)

        payment_data = {
            "partner_id" : customer.get('id'),
            "date" : datetime.now().strftime("%Y-%m-%d"),
            "journal_id" : journal.id,
            "payment_method_line_id" : metodos.id,                
            "amount" : amount,
            "pos_session_id" : pos_session_id,
            "payment_type" : "inbound",
            "ref" : invoice.get('name')
        }

        if forma_pago:
            payment_data.update({"l10n_mx_edi_payment_method_id" : forma_pago.id})

        _log.info("Payment data")
        _log.info(payment_data)

        try:
            payment_id = self.create(payment_data)
        except Exception as e:
            _log.error(e)
        else:
            credit_line_id = None
            for line in payment_id.line_ids:
                # _log.info(line.name)
                # _log.info(line.account_id.name)
                # _log.info(line.debit)
                # _log.info(line.credit)

                if line.credit > 0:
                    credit_line_id = line.id

            if payment_id:

                # if forma_pago:
                #     payment_id.write({"l10n_mx_edi_payment_method_id" : forma_pago.id})

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

        # poso_inv = order_id.action_pos_order_invoice()
        # _log.info("\n La factura de la comision es ::: %s " % poso_inv)

