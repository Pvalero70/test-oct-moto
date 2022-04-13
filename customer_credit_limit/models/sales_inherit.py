# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
import werkzeug.urls


class sale_order(models.Model):
    _inherit = "sale.order"
    
    @api.onchange('partner_id')
    def _compute_total_customer_limit_total(self):
        # Buscar el adeudo en facturas ya timbradas.
        for sale in self:
            inv_domain = [
                ('move_type', '=', 'out_invoice'),
                ('partner_id', '=', sale.partner_id.id),
                ('edi_state', '=', "sent"),
                ('amount_residual', '>', 0),
            ]
            partner_invoice_signed_ids = self.env['account.move'].search(inv_domain)
            amount_due = 0
            if sale.currency_id and sale.currency_id != sale.company_id.currency_id:
                for inv in partner_invoice_signed_ids:
                    amount_due += inv.amount_residual._convert(inv.amount_residual, inv.company_id.currency_id, sale.company_id, inv.invoice_date or fields.Date.today())
            else:
                amount_due = sum(partner_invoice_signed_ids.mapped('amount_residual'))
            # Total disponible es su limite menos lo que ya debe.
            total_available = sale.partner_id.credit_limit - amount_due
            sale.update({'sale_credit_limit_customer_total': total_available})

    @api.onchange('partner_id', 'order_line')
    def _compute_approve_needed(self):
        """Method that define if de current user could confirm sale order"""
        # Saber si el usuario actual pertenece al grupo de personas que pueden validar
        if self.env.user.has_group('customer_credit_limit.group_credit_limit_accountant'):
            self.update({'approve_needed': False})
        # Si no pertenece a ese grupo entonces, necesita validación? en base al crédito disponible y el total de la venta.
        elif self.total_amount > self.sale_credit_limit_customer_total:
            self.update({'approve_needed': True})
        else:
            # Si no pertenece al grupo de validadores pero tampoco supera su crédito entonces no necesita aprobación.
            self.update({'approve_needed': False})

    sale_credit_limit_customer_total = fields.Monetary(string="Credito",compute="_compute_total_customer_limit_total", store=True)
    approve_needed = fields.Boolean(string="Necesita aprovación", copy=False, default=False)
    company_currency_id = fields.Many2one('res.currency', string="Company Currency", related="company_id.currency_id")

    def action_request_approve(self):
        """
        Método para solicitar aprobación: envía un correo electrónico a las personas encargadas de solicitar,
        éste
        :return:
        """
        for rec in self:
            ctx = {}
            ctx['email_to'] = rec.partner_id.email
            ctx['email_from'] = self.env.user.user_id.email
            ctx['send_email'] = True
            ctx['partner_id'] = rec.partner_id.id
            template = self.env.ref('hr_recruitment_custom.job_applicant_acknowledgment')
            template.with_context(ctx).send_mail(
                rec.id, force_send=True, raise_exception=False)


