# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class SalesmanCommission(models.Model):
    _name = "salesman.commission"
    _description = "Concentrado de comisiones comisiones de vendedores"

    salesman_id = fields.Many2one('res.partner', string="Vendedor")
    
    company_id = fields.Many2one('res.company', string="Compañía")
    line_ids = fields.One2many('salesman.commission.line', 'monthly_commission_id', string="Comisiones")
    amount_total = fields.Float(string="Total de comision")
    state = fields.Selection([
        ('to_pay', "Por pagar"),
        ('paid', "Pagada")], string="Estado")
    payment_date = fields.Datetime(string="Fecha de pago")


class SalesmanCommissionLine(models.Model):
    _name = "salesman.commission.line"
    _description = "Comisiones de vendedor por mes"

    monthly_commission_id = fields.Many2one('salesman.commission', string="Comision mensual", help="Acumulado mensual")
   
    salesman_id = fields.Many2one('res.partner', related="monthly_commission_id.salesman_id")
    amount = fields.Float(string="Total de comisión")
    invoice_id = fields.Many2one('account.move', string="Factura")
    commission_date = fields.Datetime(string="Hora de comisión")
    

