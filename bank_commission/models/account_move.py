# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import logging
_log = logging.getLogger("___name: %s" % __name__)


class AccountMoveBc(models.Model):
    _inherit = "account.move"

    # @pai.model
    # def is_inv_with_commission(self, inv_id=None, spm_id=None, pos_config=None):
    #
    #     _log.info("\n\n Se necesita comision ???=  .... ")
    #     _log.info(
    #         "\n ID FACTRA:: %s \n ID METODO DE PAGO SELECCIONADO :: %s \n POS CONF:: %s" % (inv_id, spm_id, pos_config))
    #     if inv_id is not None and spm_id is not None and pos_config is not None:
    #         invoice = self.env['account.move'].browse(inv_id)
    #         selected_payment_method = self.env['pos.payment.method']
    #         pos_config
    #     return True

    @api.model
    def calc_commission_amount(self, inv_id=None, spm_id=None, posconfigid=None):
        """
        invoice
        Selected payment method
        pos config
        Método que calcula las comisiones que deben pagarse, dado un método de pago y las lineas de la factura.
        calcula el precio del producto comisión (antes de impuestos)
        y calcula el monto a pagar (despuúes de impuestos)
        :return: regresa un diccionario que nos dice
        """
        _log.info("\n ID FACTRA:: %s \n ID METODO DE PAGO SELECCIONADO :: %s \n POS CONF:: %s" % (inv_id, spm_id, posconfigid))
        if inv_id is not None and spm_id is not None:

            invoice = self.env['account.move'].browse(inv_id)
            selected_payment_method = self.env['pos.payment.method'].browse(spm_id)
            # pos_config = self.env['pos.config'].browse(pos_config)
            spm_product_categs = selected_payment_method.product_cate_commission_ids
            categs = spm_product_categs.ids + spm_product_categs.mapped('child_id').ids
            _log.info("\n Categorias analizadas:: %s" % categs)
            # Buscar las lineas de la factura que tengan un producto con la categoría seteada en el método de pago.
            lines_with_commission = invoice.invoice_line_ids.filtered(lambda li: li.product_id.categ_id.id in categs)
            apply_commission = True if len(lines_with_commission) > 0 else False
            product_commission_amount = 0
            payment_commission_amount = 0

            # En este punto sabemos que hay lineas a las que se les va a calcular la comision.
            if not selected_payment_method.bank_commission_method:
                apply_commission = False
            elif selected_payment_method.bank_commission_method == "fixed":
                # mapear los impuestos que faltan para poder poner ambas cantidades...
                # por lo general aplican solo el IVA pero no vaya a ser mejor hay que hacerlo dinamico.. xD
                commission_amount = selected_payment_method.bank_commission_amount
            elif selected_payment_method.bank_commission_method == "percentage":
                subtotal_amount_lines = sum(lines_with_commission.mapped('price_subtotal'))
                total_amount_lines = sum(lines_with_commission.mapped('price_total'))
                product_commission_amount = subtotal_amount_lines * (selected_payment_method.bank_commission_amount/100)
                payment_commission_amount = total_amount_lines * (selected_payment_method.bank_commission_amount/100)
            return {
                "apply_commission": apply_commission,
                "product_commission_amount": product_commission_amount,
                "payment_commission_amount": payment_commission_amount
            }
        return {"apply_commission": False}


#     @api.model_create_multi
#     def create(self, vals_list):
#         # OVERRIDE
#         invoices = super(AccountMoveBc, self).create(vals_list)
#         _log.info("\n TODAS LAS FACTURAS ::: %s" % invoices)
#         for inv in invoices:
#             _log.info("\n Factura a revisar::: (%s) $s " % inv.name, inv)
#             if not inv.pos_order_ids:
#                 continue
#             _log.info("\n Factura del punto de venta")
#             invoice_pos_payment_methods = inv.pos_order_ids.mapped('payment_method_id').filtered(lambda bcm: bcm.bank_commission_method != False)
#             if not invoice_pos_payment_methods:
#                 continue
#             self.create_bc_inv(inv)
#         return invoices
#
#     @api.model
#     def create_bc_inv(self, inv):
#         _log.info("\n Creando comisión para la factura:: %s " % inv)