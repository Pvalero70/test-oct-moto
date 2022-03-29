# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


class AccountMoveCustoms(models.Model):
    _inherit = "account.move"

    @api.model_create_multi
    def create(self, vals_list):
        _log.info("\n DEBUG [BEFORE] :: %s " % vals_list)
        for vals in vals_list:
            inv_journal_id = None
            # Nos aseguramos que sea una factura de cliente.
            if 'move_type' not in vals or vals['move_type'] != 'out_invoice':
                continue
            # Iteramos las lineas de la factura para encontrar un producto con diario establecido en su categoría.
            for line in vals['line_ids']:
                pro_id = line[2]['product_id']
                product_id = self.env['product.template'].browse(pro_id)

                # Identificamos el diario mediante la lista de productos.
                journal_id = product_id.categ_id.target_journal_id if product_id.categ_id and product_id.categ_id.target_journal_id else False
                if not journal_id:
                    continue
                inv_journal_id = journal_id.id
                break

            # Cambiamos el diario en vals.
            if inv_journal_id is not None:
                vals['journal_id'] = inv_journal_id

        _log.info("\n DEBUG [AFTER] :: %s " % vals_list)
        invoices =super(AccountMoveCustoms, self).create(vals_list)
        # for inv in invoices:
        #     # Identificar si es una factura de venta...
        #     if inv.move_type not in ['out_invoice']:
        #         continue
        #     # if inv.name and inv.name != '/':
        #     #     continue
        #     # Buscamos la primer categoría encontrada que tenga asignada un diario.
        #     product_id = inv.invoice_line_ids.mapped('product_id').filtered(
        #         lambda p: p.categ_id.target_journal_id is not False)
        #     if product_id:
        #         journal_id = product_id[:1].categ_id.target_journal_id
        #         _log.info("\n Nombre factura::: %s \n Diario:: %s  \n Nombre a mostrar diario:: %s " %
        #                   (inv.name, inv.journal_id, inv.journal_id.name))
        #         # inv.journal_id = journal_id.id
        #         _log.info("\n\n Diario asignado:: %s - %s  " % (inv.journal_id.name, inv.journal_id))
        return invoices
