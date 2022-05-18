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

    def _validate_session(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        
        _logger.info("## SOBRE ESCRIBE VALIDATE SESION ###")
        _logger.info(balancing_account)
        _logger.info(amount_to_balance)
        _logger.info(bank_payment_method_diffs)

        res = super(PosSession, self)._validate_session(balancing_account, amount_to_balance, bank_payment_method_diffs)

        # self.clear_session_close_moves_payments()

        return res

    def clear_session_close_moves_payments(self):

        _logger.info("Metodo que se ejecuta cuando se cierra una session")

        _logger.info("###Pagos relacionados####")
        move_line_ids = []
        payments_rel = self.env['account.payment'].search([('pos_session_id', '=', self.id)])
        monto_payment_pos = 0
        pago_pos_close = None
        payment_partner_list = []
        payment_partner_move_list = []
        session_move = self.move_id
        session_journal = session_move.journal_id

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
                pago_pos_close = payment

            # _logger.info(payment.date)
            # _logger.info(payment.journal_id.name)
            # _logger.info("## Asiento ##")
            # _logger.info(payment.move_id.name)
            
            for move_line in payment.move_id.line_ids:
                
                if payment.partner_id:
                    move_line_ids.append(move_line.id)

        if pago_pos_close:
            # _logger.info("## PAGO POS CLOSE ##")
            # _logger.info(pago_pos_close.name)

            pago_pos_close.action_draft()
            # _logger.info("## Se cambia a borrador ##")
            # _logger.info(pago_pos_close.amount)
            pago_pos_close.amount = pago_pos_close.amount - monto_payment_pos
            # _logger.info("## Se actualiza monto ##")
            # _logger.info(pago_pos_close.amount)
            pago_pos_close.action_post()
            # _logger.info("## Se vuelve a confirmar ##")

        all_related_moves = self._get_related_account_moves()
        lines = self.env['account.move.line']
        related_ids = all_related_moves.mapped('line_ids').ids
        
        _logger.info("## Lineas relacionadas a la sesion ##")
        _logger.info(related_ids)
        
        _logger.info("## Lineas de pagos ##")
        _logger.info(move_line_ids)

        set_related_ids = set(related_ids)
        set_move_line_ids = set(move_line_ids)
        related_ids = list(set_related_ids - set_move_line_ids)

        _logger.info("## Lineas sin pago ##")
        _logger.info(related_ids)

        move_lines = lines.search([('id', 'in', related_ids)])

        if payment_partner_list:
            _logger.info("Se cambia a borrador el asiento del POS")
            session_move.button_draft()

        _logger.info("Se empiezan a procesas la lista de los pagos")
        for payment in payment_partner_list:

            payment_amount = payment.amount

            credit_lines = move_lines.filtered(lambda line: line.journal_id.id == session_journal.id and line.credit > 0)
            debit_lines = move_lines.filtered(lambda line: line.journal_id.id == session_journal.id and line.debit > 0)
            # debit_line_id = debit_lines[0].id
            # debit_line_monto = debit_lines[0].debit
            # debit_move_id = debit_lines[0].move_id

            _logger.info("Credit Lines")
            _logger.info(credit_lines)

            _logger.info("Debit Lines")
            _logger.info(debit_lines)

            # monto_credit = 0
            update_lines = []
            sum_credits_updated = 0
            credit_pending = payment_amount            
            for line in credit_lines:

                if credit_pending > 0 and line.partner_id.id == payment.partner_id.id:
                   
                    _logger.info("Se actualizan los montos")

                    if line.credit >= payment_amount:
                        new_credit = line.credit - payment_amount
                        sum_credits_updated += payment_amount
                    else:
                        credit_pending = credit_pending - line.credit
                        sum_credits_updated += line.credit
                        new_credit = 0
                    update_lines.append((1, line.id, {"credit" : new_credit}))

            debit_line = None
            for line in debit_lines:
                if line.debit >= sum_credits_updated:
                    debit_line = line
                    break
            if debit_line:
                new_debit = debit_line.debit - sum_credits_updated
                update_lines.append((1, debit_line.id, {"debit" : new_debit}))
            else:
                debit_pending = sum_credits_updated
                for line in debit_lines:
                    if debit_pending > 0:
                        if line.debit >= debit_pending:
                            new_debit = line.debit - sum_credits_updated
                        else:
                            debit_pending = debit_pending - line.debit
                            new_debit = 0
                        update_lines.append((1, line.id, {"debit" : new_debit}))

            if update_lines and session_move:
                _logger.info("Se intenta actualizar lineas")
                _logger.info(update_lines)
                try:
                    session_move.write({"line_ids" : update_lines})
                except Exception as e:
                    session_move.action_post()
                    _logger.info("Ocurrio un error al actualizar el movimiento")
                    _logger.info(e)
                else:
                    _logger.info("Se ha actualizado correctamente.")
                    session_move.action_post()
                    # Descomentar para borrar el asiento
                    # for line in debit_move_id.line_ids:
                    #     if line.debit == 0 and line.credit == 0:
                    #         line.unlink()
                    # if not debit_move_id.line_ids:
                    #     _logger.info("Se elimina move porque no tiene lineas")
                    #     debit_move_id.unlink()
                    # else:
                    #     debit_move_id.action_post()
            