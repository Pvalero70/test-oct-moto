# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


class AccountMoveCustoms(models.Model):
    _inherit = "account.move"

    @api.model_create_multi
    def create(self, vals_list):
        invoices =super(AccountMoveCustoms, self).create(vals_list)
        for inv in invoices:
            # Identificar si es una factura de venta...
            if inv.move_type not in ['out_invoice']:
                continue
            # Buscamos en las lineas productos que pertenezcan a cierta categoría, por ahora R y S.
            prods_line = inv.invoice_line_ids.mapped('product_id')
            s_products = prods_line.filtered(lambda p: p.categ_id.display_name.upper().find(
                'ACCESORIOS') >= 0 or p.categ_id.display_name.upper().find('REFACCIONES') >= 0)
            if s_products:
                # Identificamos el diario con code in ['s', 'S']
                journal_id = self.env['account.journal'].search([('code', 'in', ['s', 'S'])], limit=1)
                inv.journal_id = journal_id.id
                break
            r_products = prods_line.filtered(lambda p: p.categ_id.display_name.upper().find(
                'REPARACI') >= 0)
            if r_products:
                # Identificamos el diario con code in ['R', 'r']
                journal_id = self.env['account.journal'].search([('code', 'in', ['r', 'R'])], limit=1)
                inv.journal_id = journal_id.id
                break
        return invoices