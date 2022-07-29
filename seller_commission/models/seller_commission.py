# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging

_log = logging.getLogger("\n\n---___---___--__-···>> Seller Commission:: ")


class SellerCommission(models.Model):
    _name = "seller.commission"
    _description = "Concentrado de comisiones comisiones de vendedores"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    """
    1 millón de ventas en motocicletas = 4%
    4 millones de ventas en motocicletas = 8%
    Se paga una comisión por moto que está liquidada, siempre y cuando el pedido esté facturado y pagada
    
    En general es necesario agrupar las lineas por categoría, de tal forma que se tenga una linea por categoría y por ende una suma; 
    la regla deberá ir cambiando cuando la linea vaya cambiando su total; 
    
    Por lo anterior, Se debe establecer un constrain en las reglas para que cuando una categoría sea establecida con un método de calculo,
    no pueda ser establecida otra regla con la misma categoría pero con diferente método; es decir: una categoría siempre tendrá un mismo método. 
    """

    seller_id = fields.Many2one('res.partner', string="Vendedor", check_company=True)
    company_id = fields.Many2one('res.company', string="Compañía", default=lambda self: self.env.company)
    line_ids = fields.One2many('seller.commission.line',
                               'monthly_commission_id',
                               string="Comisiones", tracking=True,
                               help="Lineas de concentrado de sumas, agrupado por categorías. ")

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
        for reg in self:
            if not reg.calc_method or not reg._origin:
                continue
            method = {
                'fixed': 'Monto fijo',
                'percent_utility': '% Utilidad',
                'percent_sale': '% Venta',
            }
            rule_name = "%s %s - %s" % (method[reg.calc_method], reg.amount_factor, reg.id)
            reg.name = rule_name

    @api.constrains('calc_method', 'product_categ_ids')
    def check_commission_rules_categ(self):
        """
        Método que revisa que las categorías establecidas en dicho registro no sean
        encontradas en otras reglas con un método de calculo diferente;
        :return:
        """
        def sublista(l1, l2):
            # Regresa los elementos de la primer lista que están en la segunda.
            return [x for x in l1 if x in l2]
        other_rules = self.env['seller.commission.rule'].search([
            ('company_id', '=', self.company_id.id),
            ('calc_method', '!=', self.calc_method),
        ]).filtered(lambda r: len(sublista(self.product_categ_ids, r.product_categ_ids)) > 0)
        if other_rules:
            raise ValidationError(_("Las reglas %s entran en conflicto con la regla que está intentando crear o editar,"
                                    " ya que algunas de sus categorías de productos que intenta poner en la regla que"
                                    " está editando o creando se encuentran en dichas reglas con conflicto pero con"
                                    " diferente método de calculo." % other_rules.mapped('name')))


