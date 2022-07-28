# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import logging

_log = logging.getLogger("\n\n---___---___--__-···>> Seller Commission:: ")


class SellerCommission(models.Model):
    _name = "seller.commission"
    _description = "Concentrado de comisiones comisiones de vendedores"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    seller_id = fields.Many2one('res.partner', string="Vendedor", check_company=True)
    company_id = fields.Many2one('res.company', string="Compañía", default=lambda self: self.env.company)
    line_ids = fields.One2many('seller.commission.line', 'monthly_commission_id', string="Comisiones", tracking=True)
    amount_total = fields.Float(string="Total de comision", tracking=True)
    state = fields.Selection([
        ('to_pay', "Por pagar"),
        ('paid', "Pagada")], tracking=True, string="Estado")
    payment_date = fields.Datetime(string="Fecha de pago", tracking=True)
    current_month = fields.Selection([
        ("0", ""),
        ("1", 'Enero'),
        ("2", "Febrero"),
        ("3", "Marzo"),
        ("4", "Abril"),
        ("5", "Mayo"),
        ("6", "Junio"),
        ("7", "Julio"),
        ("8", "Agosto"),
        ("9", "Septiembre"),
        ("10", "Octubre"),
        ("11", "Noviembre"),
        ("12", "Diciembre")
    ], string="Mes", tracking=True, required=True, )
    commission_quantity_lines = fields.Integer(string="Cantidad de conceptos", tracking=True)


class SellerCommissionLine(models.Model):
    _name = "seller.commission.line"
    _description = "Comisiones de vendedor por mes"

    monthly_commission_id = fields.Many2one('seller.commission', string="Comision mensual", help="Acumulado mensual")
   
    seller_id = fields.Many2one('res.partner', related="monthly_commission_id.seller_id")
    amount = fields.Float(string="Total de comisión")
    invoice_id = fields.Many2one('account.move', string="Factura")
    commission_date = fields.Datetime(string="Hora de comisión")
    comm_method = fields.Many2one('seller.commission.rule', string="Método de calculo")
    

class SellerCommissionRule(models.Model):
    _name = "seller.commission.rule"
    _description = "Reglas de calculo para comisiones de vendedores."

    name = fields.Char(string="Nombre", compute="_compute_rule_name", store=False)
    calc_method = fields.Selection([('fixed', 'Monto fijo'),
                                    ('percent_utility', '% Utilidad'),
                                    ('percent_sale', '% Venta')], string="Método", required=True)
    company_id = fields.Many2one('res.company', string="Compañía", default=lambda self: self.env.company)
    product_categ_ids = fields.Many2many('product.category', string="Categorías de productos", required=True)
    amount_factor = fields.Float(string="Factor")
    amount_start = fields.Float(string="A partir de ($)", help="A Partir de esta cantidad entra esta regla. Si se configura como cero se considera monto libre.")

    # @api.onchange('calc_method', 'amount_factor')
    def _compute_rule_name(self):
        if not self.calc_method or not self._origin:
            return
        method = {
            'fixed': 'Monto fijo',
            'percent_utility': '% Utilidad',
            'percent_sale': '% Venta',
        }
        rule_name = "%s %s - %s" % (method[self.calc_method], self.amount_factor, self.id)
        self.name = rule_name
