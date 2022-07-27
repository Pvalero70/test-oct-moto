# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class SellerCommission(models.Model):
    _name = "seller.commission"
    _description = "Concentrado de comisiones comisiones de vendedores"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    seller_id = fields.Many2one('res.partner', string="Vendedor", check_company=True)
    company_id = fields.Many2one('res.company', string="Compañía")
    line_ids = fields.One2many('seller.commission.line', 'monthly_commission_id', string="Comisiones", track_visibility='onchange')
    amount_total = fields.Float(string="Total de comision", track_visibility='onchange')
    state = fields.Selection([
        ('to_pay', "Por pagar"),
        ('paid', "Pagada")], track_visibility='onchange', string="Estado")
    payment_date = fields.Datetime(string="Fecha de pago", track_visibility='onchange')
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
    ], string="Mes", track_visibility='onchange', required=True, )
    commission_quantity_lines = fields.Integer(string="Cantidad de conceptos", track_visibility='onchange')


class SellerCommissionLine(models.Model):
    _name = "seller.commission.line"
    _description = "Comisiones de vendedor por mes"

    monthly_commission_id = fields.Many2one('seller.commission', string="Comision mensual", help="Acumulado mensual")
   
    seller_id = fields.Many2one('res.partner', related="monthly_commission_id.seller_id")
    amount = fields.Float(string="Total de comisión")
    invoice_id = fields.Many2one('account.move', string="Factura")
    commission_date = fields.Datetime(string="Hora de comisión")
    

