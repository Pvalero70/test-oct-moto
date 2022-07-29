# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import logging

_log = logging.getLogger("--__--__-->>> Account Move:: ")


class AccountMoveSc(models.Model):
    _inherit = "account.move"

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id')
    def _compute_amount(self):
        res = super(AccountMoveSc, self)._compute_amount()
        for move in self:
            if move.amount_residual == 0 and move.move_type == "out_invoice" and move.payment_state == "in_payment":
                self.create_seller_commission(move)
        return res

    @api.model
    def create_seller_commission(self, invoice_id):
        _log.info("Creando comision para factura: %s " % invoice_id)
        comm_total_amount = 0

        # Buscamos en los POS ORDER, luego SALE ORDER y finalmente REPARATION ORDER.
        pos_order = self.env['pos.order'].search([('account_move', '=', invoice_id.id)])
        if pos_order:
            _log.info(" PEDIDO TPV :: %s " % pos_order)
            for line in pos_order.lines:
                # Buscar la regla que mejor se ajuste.
                # Calcular en base a la regla
                
            return
        # for line in invoice_id.invoice_line_ids:
