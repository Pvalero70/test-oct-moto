# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


class AccountMoveCustoms(models.Model):
    _inherit = "account.move"

    @api.model_create_multi
    def create(self, vals_list):
        _log.info("\n DEBUG [create invoice before vals] :: %s " % vals_list)
        invoices =super(AccountMoveCustoms, self).create(vals_list)
        for inv in invoices:
            # Identificar si es una factura de venta...
            if inv.move_type not in ['out_invoice']:
                continue
            # Buscamos la primer categoría encontrada que tenga asignada un diario.
            product_id = inv.invoice_line_ids.mapped('product_id').filtered(
                lambda p: p.categ_id.target_journal_id is not False)
            if product_id:
                journal_id = product_id[:1].categ_id.target_journal_id
                _log.info("\n Nombre factura::: %s \n Diario:: %s  \n Nombre a mostrar diario:: %s " %
                          (inv.name, inv.journal_id, inv.journal_id.name))
                inv.journal_id = journal_id.id
                _log.info("\n\n Diario asignado:: %s - %s  " % (inv.journal_id.name, inv.journal_id))
        return invoices
