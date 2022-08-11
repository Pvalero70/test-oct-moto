# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging

_log = logging.getLogger("\n\n---___---___--__-···>> SALE Seller Commission:: ")


class SaleOrderSc(models.Model):
    _inherit = "sale.order"

    def create_commission(self, invoice=None, order=None):
        """
        Método que crea una comision de una factura, o bien agrega una linea de comisión (concepto)
        a una comisión ya existente.
        :param invoice:
        :param order:
        :return:
        """
        _log.info("Creando comisión de vendedor")
        # Revisamos si existen reglas para los productos de las lineas
        line_product_categories = self.order_line.mapped('product_id').mapped('categ_id').mapped('parent_id')
        if not line_product_categories:
            return False
        all_rule_ids = self.env['seller.commission.rule'].search([('company_id', '=', self.env.company.id)])
        if not all_rule_ids:
            return False
        prelines = []
        for sline in self.order_line:
            line_rules = all_rule_ids.filtered(lambda r: sline.product_id.categ_id.parent_id.id in r.product_categ_ids.ids)
            if not line_rules:
                _log.info("\nNo aplican reglas para esta linea.")
                continue
            line_comm_method = line_rules.mapped('calc_method')
            calc_amount = 0
            if line_comm_method in ["fixed", "percent_sale"]:
                # Para el fijo y porcentaje de venta se utiliza el total de la venta por linea (subtotal)
                # para sumarse a otras lineas de comisión y poder determinar cual es la regla que aplica.
                # El método de calculo no cambiará.
                calc_amount = sline.price_subtotal
            else:
                # Para poder determinar que regla exactamente aplica es necesario considerar el margen
                # de ganancia.
                calc_amount = sline.margin

            # Construimos la prelinea.
            preline = {
                'amount': calc_amount,
                'categ_id': sline.product_id.categ_id.parent_id.id,
                'invoice_id': invoice
            }
            prelines.append((0, 0, preline))


