# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import logging

_log = logging.getLogger("--__--__-->>> Account Move:: ")


class AccountMoveSc(models.Model):
    _inherit = "account.move"

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

    @api.model
    def create_seller_preline_commission(self, invoice_id):
        _log.info("Creando comision para factura: %s " % invoice_id)

        # Buscamos en los POS ORDER, luego SALE ORDER y finalmente REPARATION ORDER.
        pos_order = self.env['pos.order'].search([('account_move', '=', invoice_id.id)])
        if pos_order:

            rule_ids = self.env['seller.commission.rule'].search([('company_id', '=', pos_order.company_id.id)])
            pre_lines = []
            for line in pos_order.lines:
                # El producto de la linea tiene una regla para su categoría ?  padre de la categoría del producto. 
                line_rules = rule_ids.filtered(lambda x: line.product_id.categ_id.parent_id.id in x.product_categ_ids.ids)
                if not line_rules:
                    continue
                # Creamos una prelinea..
                # Seleccionamos el mètodo y el monto; en el caso de que sea fixed o percent_sale se pasa el amount,
                # en otro caso pasamos el utility.

                # Este amount servirá como base para sumarse con otras lineas y poder seleccionar
                # cual es la regla exacta que será seleccionada.
                calc_method = line_rules[0].calc_method
                _log.info("\n Método de calculo. ")
                if calc_method == "fixed":
                    calc_amount = line.price_subtotal_incl
                elif calc_method == "percent_sale":
                    calc_amount = line.price_subtotal_incl
                else: # percen_utility
                    calc_amount = line.margin

                preline = {
                    'amount': calc_amount,
                    'categ_id': line.product_id.categ_id.parent_id.id,
                    'invoice_id': invoice_id.id
                }
                pre_lines.append((0, 0, preline))

            # Buscamos una comision del mismo mes y mismo año que esté sin pagar; si no existe
            # entonces la creamos.

            commission = self.env['seller.commission']
            commission_id = commission.search([
                ('seller_id', '=', False),
                ('current_month', '=', fields.Date().today().month)])
            return
        # for line in invoice_id.invoice_line_ids:
