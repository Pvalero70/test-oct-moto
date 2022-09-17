# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import timedelta

from odoo import api, fields, models, _, Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare

import logging

_logger = logging.getLogger(__name__)

class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def obtener_facturas_anticipo(self, partner_id, pos_config_id):
        _logger.info(self)
        _logger.info(partner_id)
        _logger.info(pos_config_id)
        pos_config = self.env['pos.config'].search([('id', '=', pos_config_id)])
        pos_name = pos_config.name
        crm_team = self.env['crm.team'].search([('name', '=', pos_name)], limit=1)
        product_credit = pos_config.credit_note_product_id
        domain = [
            ('invoice_line_ids.product_id', 'ilike', product_credit.id), 
            ('partner_id', '=', partner_id), 
            ('move_type', '=', 'out_invoice')]
        
        if crm_team:
            _logger.info("Filtra por punto de venta")
            domain.append(('team_id', '=', crm_team.id))
        
        _logger.info(domain)

        facturas = self.env['account.move']
        invoices = facturas.search(domain)

        anticipo_ids = []
        for invoice in invoices:
            cfdi_uuid = invoice.l10n_mx_edi_cfdi_uuid
            new_domain = [
                ('partner_id', '=', partner_id), 
                ('move_type', '=', 'out_invoice'),
                ('l10n_mx_edi_origin', 'like', cfdi_uuid),
                ('id', 'not in', invoices.ids)
            ]
            _logger.info("## New domain ##")
            _logger.info(new_domain)
            res = facturas.search(new_domain, limit=1)
            if not res:
                anticipo_ids.append(invoice.id)
        
        _logger.info("## Anticipo Ids ##")
        _logger.info(anticipo_ids)

        invoice_ids = []
        if anticipo_ids:
            invoice_ids = self.env['account.move'].search(
                [
                    ('id', 'in', anticipo_ids)
                ]
            )
        # invoice_ids = self.env['account.move'].search([('invoice_line_ids.product_id', 'ilike', product_credit.id), ('partner_id', '=', partner_id), ('move_type', '=', 'out_invoice'), ('state', '=', 'not_paid')])
        
        invoice_list = []
        if invoice_ids:
            
            _logger.info('## Facturas de anticipo ##')
            _logger.info(invoice_ids.ids)

            for inv in invoice_ids:
                invoice_list.append({
                    "id" : inv.id,
                    "name" : inv.name,
                    "total" : inv.amount_total,
                    "residual" : inv.amount_residual,
                })
        return invoice_list



    def _validate_session(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        
        _logger.info("## SOBRE ESCRIBE VALIDATE SESION ###")
        _logger.info(balancing_account)
        _logger.info(amount_to_balance)
        _logger.info(bank_payment_method_diffs)

        res = super(PosSession, self)._validate_session(balancing_account, amount_to_balance, bank_payment_method_diffs)

        # self.clear_session_close_moves_payments()

        return res
    
    

    def _check_invoices_are_posted(self):
        unposted_invoices = self.order_ids.account_move.filtered(lambda x: x.state != 'posted' and x.state != 'cancel')
        if unposted_invoices:
            raise UserError(_('You cannot close the POS when invoices are not posted or canceled.\n'
                              'Invoices: %s') % str.join('\n',
                                                         ['%s - %s' % (invoice.name, invoice.state) for invoice in
                                                          unposted_invoices]))

    def clear_session_close_moves_payments(self):

        _logger.info("Metodo que se ejecuta cuando se cierra una session")

        _logger.info("###Pagos relacionados####")
        move_line_ids = []
        payments_rel = self.env['account.payment'].search([('pos_session_id', '=', self.id)])
        monto_payment_pos = 0
        pago_pos_close_list = []
        pago_pos_close = None
        payment_partner_list = []
        payment_partner_move_list = []
        session_move = self.move_id
        session_journal = session_move.journal_id

        _logger.info(session_journal.name)

        if not payments_rel.ids:
            return

        for payment in payments_rel:
            _logger.info(payment.name)
            _logger.info(payment.amount)
            
            if payment.partner_id:
                _logger.info("Pago de Cliente")
                _logger.info(payment.partner_id.name)
                monto_payment_pos += payment.amount
                payment_partner_list.append(payment)
                payment_partner_move_list.append(payment.move_id)
            else:
                _logger.info("Pago de PDV")
                # pago_pos_close = payment
                pago_pos_close_list.append(payment)

            # _logger.info(payment.date)
            # _logger.info(payment.journal_id.name)
            # _logger.info("## Asiento ##")
            # _logger.info(payment.move_id.name)
            
            for move_line in payment.move_id.line_ids:
                
                if payment.partner_id:
                    move_line_ids.append(move_line.id)

        if pago_pos_close_list:
            for pago_pos_close in pago_pos_close_list:
                _logger.info("## PAGO POS CLOSE ##")
                _logger.info(pago_pos_close.name)
                _logger.info(pago_pos_close.amount)
                _logger.info(monto_payment_pos)

                if monto_payment_pos > 0 and pago_pos_close.amount >= monto_payment_pos:
                    pago_pos_close.action_draft()
                    _logger.info("## Se cambia a borrador ##")
                    _logger.info(pago_pos_close.amount)
                    pago_pos_close.amount = pago_pos_close.amount - monto_payment_pos
                    _logger.info("## Se actualiza monto ##")
                    _logger.info(pago_pos_close.amount)
                    pago_pos_close.action_post()
                    _logger.info("## Se vuelve a confirmar ##")

        lines = self.env['account.move.line']
        # all_related_moves = self._get_related_account_moves()
        # related_ids = all_related_moves.mapped('line_ids').ids
        
        # _logger.info("## Lineas relacionadas a la sesion ##")
        # _logger.info(related_ids)
        
        # _logger.info("## Lineas de pagos ##")
        # _logger.info(move_line_ids)

        # set_related_ids = set(related_ids)
        # set_move_line_ids = set(move_line_ids)
        # related_ids = list(set_related_ids - set_move_line_ids)

        # _logger.info("## Lineas sin pago ##")
        # _logger.info(related_ids)

        move_lines = lines.search([('move_id', '=', session_move.id)])

        if not payment_partner_list:
            return

        _logger.info("Se cambia a borrador el asiento del POS")
        session_move.button_draft()

        _logger.info("Se empiezan a procesas la lista de los pagos")
        sum_credits_updated = 0

        credit_lines = move_lines.filtered(lambda line: line.credit > 0)
        debit_lines = move_lines.filtered(lambda line: line.debit > 0)

        _logger.info("Credit Lines")
        _logger.info(credit_lines)
        for crl in credit_lines:
            _logger.info(crl.move_id.name)
            _logger.info(crl.account_id.name)
            _logger.info(crl.name)
            _logger.info(crl.debit)
            _logger.info(crl.credit)

        _logger.info("Debit Lines")
        _logger.info(debit_lines)
        for dbt in debit_lines:
            _logger.info(dbt.move_id.name)
            _logger.info(dbt.account_id.name)
            _logger.info(dbt.name)
            _logger.info(dbt.debit)
            _logger.info(dbt.credit)

        procesed_lines = []
        update_lines = []
        for payment in payment_partner_list:

            payment_amount = payment.amount
            # credit_pending = payment_amount
            _logger.info(f"Payment amount: {payment_amount}")

            for line in credit_lines:

                if line.id in procesed_lines:
                    _logger.info("Continue...")
                    continue
                
                if line.partner_id.id == payment.partner_id.id:
                   
                    _logger.info("Se actualizan los montos")
                    _logger.info(f"Line Credit: {line.credit}")

                    if line.credit == payment_amount:
                        new_credit = line.credit - payment_amount
                        sum_credits_updated += payment_amount
                    # else:
                    #     credit_pending = credit_pending - line.credit
                    #     sum_credits_updated += line.credit
                    #     new_credit = 0
    
                        _logger.info(f"New Credit: {new_credit}")
                        _logger.info(f"Sum Credits: {sum_credits_updated}")

                        update_lines.append((1, line.id, {"credit" : new_credit}))
                    else:
                        _logger.info(f"Else: {line.credit}")

                    procesed_lines.append(line.id)
        _logger.info("Sum credits updated")
        _logger.info(sum_credits_updated)

        lines_debit_data = []
        for line in debit_lines:
            lines_debit_data.append({
                "id" : line.id,
                "amount" : line.debit                    
            })

        sort_payment_data = []
        for payment in payment_partner_list:
            sort_payment_data.append({
                "id" : payment.id,
                "amount" : payment.amount
            })

        procesed_lines_ids = []
        pending_payments = []
        for payment in sort_payment_data:
            payment_amount = payment["amount"]
            payment_found = False
            for line in lines_debit_data:
                if line["amount"] == payment_amount:
                    new_debit = line["amount"] - payment_amount
                    line["amount"] = new_debit
                    # update_lines.append((1, debit_line.id, {"debit" : new_debit}))
                    procesed_lines_ids.append(line["id"])
                    payment_found = True
                    break
            if not payment_found:
                pending_payments.append(payment)

        if pending_payments:

            pending_payments = sorted(pending_payments, key=lambda d: d['amount'], reverse=True) 

            for payment in pending_payments:
                payment_amount = payment["amount"]

                for line in lines_debit_data:
                    if line["id"] in procesed_lines_ids:
                        continue

                    if line["amount"] >= payment_amount:                    
                        new_debit = line["amount"] - payment_amount
                        line["amount"] = new_debit                    
                        break

        for line in lines_debit_data:
            update_lines.append((1, line["id"], {"debit" : line["amount"]}))




        
        # debit_line = None
        # for line in debit_lines:
        #     if line.debit >= sum_credits_updated:
        #         debit_line = line
        #         break
        # _logger.info("Valor de debit line %s",debit_line)
        # if debit_line:
        #     _logger.info("DEBIT LINE")
        #     _logger.info(debit_line.debit)
        #     _logger.info(sum_credits_updated)
        #     new_debit = debit_line.debit - sum_credits_updated
        #     _logger.info(new_debit)                
        #     update_lines.append((1, debit_line.id, {"debit" : new_debit}))
        # else:
        #     _logger.info("ELSE")
        #     debit_pending = sum_credits_updated
        #     for line in debit_lines:
        #         if debit_pending > 0:
        #             if line.debit >= debit_pending:
        #                 new_debit = line.debit - sum_credits_updated
        #             else:
        #                 debit_pending = debit_pending - line.debit
        #                 new_debit = 0
        #             _logger.info(new_debit)
        #             update_lines.append((1, line.id, {"debit" : new_debit}))

        if update_lines and session_move:
            _logger.info("Se intenta actualizar lineas.")
            _logger.info(update_lines)
            try:
                session_move.write({"line_ids" : update_lines})
            except Exception as e:
                session_move.action_post()
                _logger.info("Ocurrio un error al actualizar el movimiento")
                _logger.info(e)
            else:
                _logger.info("## Elimina lineas en 0 ##")
                for line in session_move.line_ids:
                    _logger.info(line.name)
                    if line.debit == 0 and line.credit == 0:
                        line.unlink()
                _logger.info("Se ha actualizado correctamente.")
                _logger.info(session_move.line_ids)
                if not session_move.line_ids:
                    _logger.info("No tiene lineas")
                    session_move.button_cancel()
                else:
                    session_move.action_post()
