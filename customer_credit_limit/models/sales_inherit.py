# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
import werkzeug.urls


class sale_order(models.Model):
    _inherit = "sale.order"
    
    @api.onchange('partner_id', 'amount_total')
    def _compute_total_customer_limit_total(self):
        # Buscar el adeudo en facturas ya timbradas.
        inv_domain = [
            ('move_type', '=', 'out_invoice'),
            ('partner_id', '=', self.partner_id.id),
            ('edi_state', '=', "sent"),
            ('amount_residual', '>', 0),
        ]
        partner_invoice_signed_ids = self.env['account.move'].search(inv_domain)
        amount_due = 0
        if self.currency_id and self.currency_id != self.company_id.currency_id:
            for inv in partner_invoice_signed_ids:
                amount_due += inv.amount_residual._convert(inv.amount_residual, inv.company_id.currency_id, self.company_id, inv.invoice_date or fields.Date.today())
        else:
            amount_due = sum(partner_invoice_signed_ids.mapped('amount_residual'))
        # Total disponible es su limite menos lo que ya debe.
        total_available = self.partner_id.credit_limit - amount_due
        self.update({'sale_credit_limit_customer_total': total_available})
        # Si el total disponible es menor que el total del pedido de venta, necesita aprobación.
        if total_available < self.amount_total:
            self.update({'approve_needed': True})
        else:
            # Evaluar al usuario logeado para ver si él necesita aprobación.
            self.update({'approve_needed': False})
    
    sale_credit_limit_customer_total = fields.Monetary(string="Credito",compute="_compute_total_customer_limit_total")
    approve_needed = fields.Boolean(string="Necesita aprovación", copy=False, default=False)
    is_approved = fields.Boolean(string="aprobado.")
    company_currency_id = fields.Many2one('res.currency', string="Company Currency", related="company_id.currency_id")

    def action_request_approve(self):
        """
        Método para solicitar aprobación: envía un correo electrónico a las personas encargadas de solicitar,
        éste
        :return:
        """
        ## Piensa que un grupo no puede hacer invisible al botón porque ¿que pasa si no necesita venta? necesita analizar eso desde python.
        ## ¿que usuario está visualizando la cotización? usuario sin permiso necesita aprobación, usuario con permiso no necesita aprobación.
        ## solicitar aprobación solo manda un correo a las personas que tienen el permiso para aprobar.
        pass
        # result = self.env['res.config.settings'].search([],order="id desc", limit=1)
        # if result.sale_approve == 'after':
        #     self.write({
        #         'state': 'sale',
        #         'date_order': fields.Datetime.now()
        #     })
        #     return True
        # elif result.sale_approve == 'before' :
        #     res = super(sale_order, self).action_confirm()
        #     return res

        
    # def action_confirm(self):
    #     result = self.env['res.config.settings'].search([],order="id desc", limit=1)
    #     date_today = fields.datetime.now().date()
    #     due_invoice = self.env['account.move'].search([('move_type','=','out_invoice'),('invoice_date_due','<',date_today),('state','=','posted'),('partner_id','=',self.partner_id.id)])
    #
    #     if self.currency_id and self.currency_id != self.company_id.currency_id:
    #         amount = self.currency_id._convert(self.amount_total, self.company_id.currency_id, self.company_id, self.date_order or fields.Date.today())
    #         total = self.partner_id.credit + amount
    #     else:
    #         total = self.partner_id.credit + self.amount_total
    #
    #     flag = False
    #     res = True
    #     if result.sale_approve == 'after' :
    #         self.show_approve =True
    #         if self.sale_credit_limit_customer <= total:
    #             res = super(sale_order, self).action_confirm()
    #             self.state = 'to_be_approved'
    #             flag = True
    #         if result.due_date_check :
    #             if due_invoice and flag == False:
    #                 res = super(sale_order, self).action_confirm()
    #                 self.state = 'to_be_approved'
    #                 flag = True
    #         if flag == False :
    #             res = super(sale_order, self).action_confirm()
    #         return res
    #     elif result.sale_approve == 'before' :
    #         if self.sale_credit_limit_customer <= total:
    #             self.state = 'to_be_approved'
    #             flag = True
    #         if result.due_date_check :
    #             if due_invoice and flag == False:
    #                 self.state = 'to_be_approved'
    #                 flag = True
    #         if flag == False :
    #             res = super(sale_order, self).action_confirm()
    #     return res
