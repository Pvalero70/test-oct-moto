# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
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
    
    @api.model
    def validar_saldo_permitido(self, values):
        _log.info("## VALIDAR SALDO PAGADO ##")
        values = values.get('vals', {})
        _log.info(values)
        customer = values.get('partner')
        partner_id = customer.get('id')

        fecha_hoy = datetime.now()
        fecha_6_months = fecha_hoy - timedelta(days=180)
        fecha_6_months_str = fecha_6_months.strftime('%Y-%m%d %H:%M:%S')

        facturas = self.search([('type', '=', 'out_invoice'), ('partner_id', '=', partner_id), ('payment_state', 'in', ['partial', 'in_payment', 'paid']), ('invoice_date', '>=', fecha_6_months_str)])

        monto_pagado = 0
        if facturas:
            for f in facturas:
                pagado = float(f.amount_total) - float(f.amount_residual)
                if pagado > 0:
                    monto_pagado += pagado

        return monto_pagado
