# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
import logging
_log = logging.getLogger("___name: %s" % __name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def js_assign_outstanding_line(self, line_id):
        _log.info(self)
        _log.info(line_id)
        move_line = self.env['account.move.line'].browse(line_id)
        _log.info(move_line.account_id.id)
        _log.info(move_line.account_id.name)
        _log.info(move_line.debit)
        _log.info(move_line.credit)

        return super(AccountMove, self).js_assign_outstanding_line(line_id)
    
    # def create_credit_note_pos(self, data):
        # move_type = 'out_refund'