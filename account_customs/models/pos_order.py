# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


class PosOrderC(models.Model):
    _inherit = "pos.order"

    def _prepare_invoice_vals(self):
        vals = super(PosOrderC, self)._prepare_invoice_vals()
        # Revisamos aquí el diario.
        # Revisamos los produtos de la orden de venta
        # product_id = self.lines.mapped('product_id').filtered(
        #     lambda p: p.categ_id.target_journal_id is not False)
        # if product_id:
        #     journal_id = product_id[:1].categ_id.target_journal_id
        #     # Asignamos el diario a los datos de la factura.
        #     if journal_id:
        #         _log.info("\n\n Asignando el diario: %s " % journal_id)
        #         vals['journal_id'] = journal_id.id

        # ====== CAMBIO DE LOGICA ==========
        # OBtenemos la caterogía del primer producto.
        # Obtenemos la ubicación de origen ( config_id.picking_type_id.default_location_src_id)

        return vals