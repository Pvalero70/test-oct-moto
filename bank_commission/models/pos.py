# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import pytz
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import logging
_log = logging.getLogger("___name: %s" % __name__)


class PosPaymentMethodBc(models.Model):
    _inherit = "pos.payment.method"

    bank_commission_method = fields.Selection([
        ("percentage", "Porcentaje"),
        ("fixed", "Monto fijo")
    ], string="Método de calculo comisión")
    bank_commission_amount = fields.Float(string="Monto de comisión")
    bank_commission_product_id = fields.Many2one('product.product', string="Concepto comisión")
    bc_journal_id = fields.Many2one("account.journal", string="Diario de comisiones")


class PosOrderBc(models.Model):
    _inherit = "pos.order"

    def _create_invoice(self, vals):
        res = super(PosOrderBc, self)._create_invoice(vals)
        # Creating new invoice for commission bank
        _log.info("\n Creando factura para.. ")
        for payment in self.payment_ids.filtered(lambda x: x.payment_method_id.bank_commission_method is not False):
            invo = self._create_bc_invoice(payment)
            _log.info("\n FACTURA POR COMISIÓN CREADA::  %s " % invo)
            if not invo:
                continue
        return res

    def _create_bc_invoice(self, payment):
        _log.info("\n Creando factura para el pago:: %s" % payment)
        # Localiza el método de calculo de la comisión
        bc_method = payment.payment_method_id.bank_commission_method
        bc_amount = payment.payment_method_id.bank_commission_amount
        bc_product_id = payment.payment_method_id.bank_commission_product_id
        bc_journal_id = payment.payment_method_id.bc_journal_id
        # Calcula el total de la factura.
        inv_total = 0
        if bc_method and bc_method == "percentage":
            inv_total = payment.amount * bc_amount
        elif bc_method and bc_method == "fixed":
            inv_total = bc_amount

        # Creamos la factura.
        timezone = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
        vals = {
            'invoice_origin': self.name,
            'journal_id': bc_journal_id.id, ###
            'move_type': 'out_invoice',
            'ref': self.name,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self._get_partner_bank_id(),
            'currency_id': self.pricelist_id.currency_id.id,
            'invoice_user_id': self.user_id.id,
            'invoice_date': self.date_order.astimezone(timezone).date(),
            'invoice_cash_rounding_id': self.config_id.rounding_method.id
        }
        invoice_lines = ((0, None, {
            'product_id': bc_product_id.id,
            'quantity': 1,
            'discount': 0,
            'price_unit': inv_total,
            'name': bc_product_id.display_name,
            'tax_ids': bc_product_id.taxes_id.ids,
            'product_uom_id': bc_product_id.uom_id.id,
        }))
        vals['invoice_line_ids'] = invoice_lines
        invoice = self.env['account.move'].sudo().with_company(self.company_id).with_context(
            default_move_type='out_invoice').create(vals)
        message = _(
            "Esta factura ha sido creada desde el punto de venta: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (
                  self.id, self.name)
        invoice.message_post(body=message)
        return invoice



