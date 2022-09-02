# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import logging

_log = logging.getLogger("--__--__-->>> Account Move:: ")


class AccountMoveSc(models.Model):
    _inherit = "account.move"

    commission_applied_id = fields.Many2one("seller.commission", string="Comision aplicada")

    has_seller_commission = fields.Boolean(string="Tiene comision", default=False)
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
            if move.amount_residual == 0 and move.move_type == "out_invoice" and move.payment_state == "in_payment" and not move.has_seller_commission:
                self.create_seller_preline_commission(move)
        return res

    def commission_test(self):
        self.create_seller_preline_commission(self)

    @api.model
    def create_seller_preline_commission(self, invoice_id):
        _log.info("Creando comision para factura: %s " % invoice_id)
        """
            >>> factura = self.env['account.move'].browse(1345)
            >>> self.env['account.move'].create_seller_preline_commission(factura)
        """
        # Buscamos en los POS ORDER, luego SALE ORDER y finalmente REPARATION ORDER.
        pos_order = self.env['pos.order'].search([('account_move', '=', invoice_id.id)])
        _log.info(" POS ORDER DE FACTURA::: %s " % pos_order)

        # Revisar que la factura no tenga una nota de crédito.

        if pos_order:
            
            # Revisar si aplica para orden de reparación o para pedido de venta.
            sale_order_ids = pos_order.lines.mapped('sale_order_origin_id')
            # repair_orders_ids = pos_order.repair_ids
            # _log.info(" VENTAS:: %s REPARACIONES:::: %s " % (sale_order_ids, repair_orders_ids))
            _log.info(" VENTAS:: %s " % sale_order_ids)
            # _log.info(" REPARACIONES:: %s " % pos_order.repair_ids)
            if sale_order_ids:
                _log.info("Viene de un pedido de venta.")
                for so in sale_order_ids:
                     # Iteramos sobre cada una de las ordenes de venta. 
                     if not so.user_id:
                        # Si el sale order no tiene vendedor. 
                        continue
                     so.create_commission(invoice=invoice_id)
            else:
                if pos_order.repair_ids:
                    _log.info("Viene de una orden de reparación::: %s " % pos_order.repair_ids)
                    for ro in pos_order.repair_ids:
                        ro.create_commission(invoice=invoice_id)
            
