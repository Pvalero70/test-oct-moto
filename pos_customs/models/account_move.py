# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
import logging
_log = logging.getLogger("___name: %s" % __name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def js_assign_outstanding_line(self, line_id):
        _log.info(self)
        _log.info(line_id)
        move_line = self.env['account.move.line'].browse(line_id)
        _log.info(move_line.account_id.id)
        _log.info(move_line.account_id.name)
        _log.info(move_line.debit)
        _log.info(move_line.credit)

        return super(AccountMove, self).js_assign_outstanding_line(line_id)

    @api.model
    def enviar_mail_advertencia_pago_permitido(self, values):
        _log.info("## ENVIAR EMAIL ##")

        params = values.get('vals')
        emails = params.get('emails', '')
        cliente = params.get('cliente', '')
        venta = params.get('venta', '')
        sucursal = params.get('sucursal', '')
        monto = params.get('monto', 0)
        
        body = "Reportar al SAT que el cliente ha rebasado el límite permitido de compra.<br>"
        body += "<br>"
        body += f"Nombre del Cliente: {cliente}" 
        body += "<br>"
        body += f"Orden de venta: {venta}" 
        body += "<br>"
        body += f"Sucursal: {sucursal}" 
        body += "<br>"
        body += f"Monto: ${monto}" 
        body += "<br>"
       
        template_obj = self.env['mail.mail']
        for email in emails.split(','):
            template_data = {
                'subject': 'Advertencia de pago permitido',
                'body_html': body,
                'email_from': self.env.user.company_id.email,
                'email_to': email
            }
            _log.info("EMAIL ORDER: Enviamos email con %s", template_data)
            template_id = template_obj.sudo().create(template_data)
            template_id.send()

    @api.model
    def validar_saldo_permitido(self, values):
        _log.info("## VALIDAR SALDO PAGADO ##")
        values = values.get('vals', {})
        _log.info(values)
        customer = values.get('partner')
        partner_id = customer.get('id')

        fecha_hoy = datetime.now()
        fecha_6_months = fecha_hoy - timedelta(days=180)
        fecha_6_months_str = fecha_6_months.strftime('%Y-%m-%d %H:%M:%S')

        facturas = self.search([('move_type', '=', 'out_invoice'), ('partner_id', '=', partner_id), ('payment_state', 'in', ['partial', 'in_payment', 'paid']), ('invoice_date', '>=', fecha_6_months_str)])

        monto_pagado = 0
        if facturas:
            for f in facturas:
                _log.info(f.name)
                pagado = float(f.amount_total) - float(f.amount_residual)
                if pagado > 0:
                    _log.info(pagado)
                    monto_pagado += pagado

        return monto_pagado
