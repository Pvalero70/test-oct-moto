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

    
    def _create_account_move(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        
        _logger.info("## SOBRE ESCRIBE CREA ACCOUNT MOVE ###")
        _logger.info(balancing_account)
        _logger.info(amount_to_balance)
        _logger.info(bank_payment_method_diffs)
        
        res = super(PosSession, self)._create_account_move(balancing_account, amount_to_balance, bank_payment_method_diffs)

        _logger.info("### DATA ###")
        _logger.info(res)

        return res

    def _accumulate_amounts(self, data):
        res = super(PosSession, self)._accumulate_amounts(data)
        _logger.info("### 1 ###")
        _logger.info(res)
        return res

    def _create_non_reconciliable_move_lines(self, data):
        res = super(PosSession, self)._create_non_reconciliable_move_lines(data)
        _logger.info("### 2 ###")
        _logger.info(res)
        return res

    def _create_bank_payment_moves(self, data):
        res = super(PosSession, self)._create_bank_payment_moves(data)
        _logger.info("### 3 ###")
        _logger.info(res)
        return res

    def _create_pay_later_receivable_lines(self, data):
        res = super(PosSession, self)._create_pay_later_receivable_lines(data)
        _logger.info("### 4 ###")
        _logger.info(res)
        return res

    def _create_cash_statement_lines_and_cash_move_lines(self, data):
        res = super(PosSession, self)._create_cash_statement_lines_and_cash_move_lines(data)
        _logger.info("### 5 ###")
        _logger.info(res)
        return res

    def _create_invoice_receivable_lines(self, data):
        res = super(PosSession, self)._create_invoice_receivable_lines(data)
        _logger.info("### 6 ###")
        _logger.info(res)
        return res

    def _create_stock_output_lines(self, data):
        res = super(PosSession, self)._create_stock_output_lines(data)
        _logger.info("### 7 ###")
        _logger.info(res)
        return res

    def _create_balancing_line(self, data):
        res = super(PosSession, self)._create_balancing_line(data)
        _logger.info("### 8 ###")
        _logger.info(res)
        return res

    

    