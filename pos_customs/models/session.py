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

        all_related_moves = self._get_related_account_moves()
        lines = self.env['account.move.line']
        move_lines = lines.search([('id', 'in', all_related_moves.mapped('line_ids').ids)])

        for line in move_lines:
            _logger.info(line.move_id.name)
            _logger.info(line.account_id.code)
            _logger.info(line.account_id.name)
            _logger.info(line.partner_id.name)
            _logger.info(line.debit)
            _logger.info(line.credit)
            _logger.info(line.name)
            _logger.info(line.matching_number)
