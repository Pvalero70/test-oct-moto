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
        
        _logger.info("## SOBRE ESCRIBE VALIDA SESION ###")
        _logger.info(balancing_account)
        _logger.info(amount_to_balance)
        _logger.info(bank_payment_method_diffs)

        return super(PosSession, self)._validate_session(balancing_account, amount_to_balance, bank_payment_method_diffs)

    def clear_session_close_moves_payments(self):

        _logger.info("Metodo que se ejecuta cuando se cierra una session")

        _logger.info("###Pagos relacionados####")
        move_line_ids = []
        payments_rel = self.env['account.payment'].search([('pos_session_id', '=', self.id)])
        monto_payment_pos = 0
        pago_pos_close = None
        payment_partner_move_list = []

        for payment in payments_rel:
            _logger.info(payment.name)
            _logger.info(payment.amount)
            
            if payment.partner_id:
                _logger.info("Pago de Cliente")
                _logger.info(payment.partner_id.name)
                monto_payment_pos += payment.amount
                payment_partner_move_list.append(payment.move_id)
            else:
                _logger.info("Pago de PDV")
                pago_pos_close = payment

            _logger.info(payment.date)
            _logger.info(payment.journal_id.name)
            _logger.info("## Asiento ##")
            _logger.info(payment.move_id.name)
            
            for move_line in payment.move_id.line_ids:
                
                if payment.partner_id:
                    move_line_ids.append(move_line.id)

        if pago_pos_close:
            _logger.info("## PAGO POS CLOSE ##")
            _logger.info(pago_pos_close.name)

            pago_pos_close.action_draft()
            _logger.info("## Se cambia a borrador ##")
            _logger.info(pago_pos_close.amount)
            pago_pos_close.amount = pago_pos_close.amount - monto_payment_pos
            _logger.info("## Se actualiza monto ##")
            _logger.info(pago_pos_close.amount)
            pago_pos_close.action_post()
            _logger.info("## Se vuelve a confirmar ##")

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

        _logger.info("Se empiezan a procesas la lista de los pagos")
        for payment in payment_partner_move_list:

            credit_lines = move_lines.filtered(lambda line: line.journal_id.id != payment.journal_id.id and line.credit > 0)
            debit_lines = move_lines.filtered(lambda line: line.journal_id.id != payment.journal_id.id and line.debit > 0)
            debit_line_id = debit_lines[0].id
            debit_line_monto = debit_lines[0].debit
            debit_move_id = debit_lines[0].move_id

            _logger.info("Credit Lines")
            _logger.info(credit_lines)
            for cline in credit_lines:
                _logger.info(cline.name)
                _logger.info(cline.debit)
                _logger.info(cline.credit)
                _logger.info(cline.partner_id.name)

            _logger.info("Debit Lines")
            _logger.info(debit_lines)

            _logger.info("Debit Line Id")
            _logger.info(debit_line_id)

            monto_credit = 0
            update_lines = []
            for line in credit_lines:

                if line.partner_id.id == payment.partner_id.id:

                    _logger.info("Linea del cliente")
                    _logger.info(line.name)
                    _logger.info(line.debit)
                    _logger.info(line.credit)
                    _logger.info(line.partner_id.name)

                    if line.move_id.state == 'posted':
                        _logger.info("Se cambia el asiento a borrador")
                        line.move_id.button_draft()

                    _logger.info("Se actualizan los montos")

                    new_credit = line.credit - monto_payment_pos
                    update_lines.append((1, line.id, {"credit" : new_credit}))
                    _logger.info(monto_credit)

                    new_debit = debit_line_monto - monto_payment_pos
                    update_lines.append((1, debit_line_id, {"debit" : new_debit}))
                    _logger.info(new_debit)

            if update_lines and debit_move_id:
                _logger.info("Se intenta actualizar lineas")
                _logger.info(update_lines)
                try:
                    debit_move_id.write({"line_ids" : update_lines})
                except Exception as e:
                    debit_move_id.action_post()
                    _logger.info("Ocurrio un error al actualizar el movimiento")
                    _logger.info(e)
                else:
                    _logger.info("Se ha actualizado correctamente.")
                    for line in debit_move_id.line_ids:
                        if line.debit == 0 and line.credit == 0:
                            line.unlink()
                    if not debit_move_id.line_ids:
                        _logger.info("Se elimina move porque no tiene lineas")
                        debit_move_id.unlink()
                    else:
                        debit_move_id.action_post()
            
            _logger.info(debit_move_id)
            if debit_move_id and debit_move_id.state != 'posted':
                _logger.info("Se intenta procesar el move id")
                try:
                    debit_move_id.action_post()
                except Exception as e:                    
                    _logger.info("Ocurrio un error al intentar publicar el asiento")
                    _logger.info(e)
