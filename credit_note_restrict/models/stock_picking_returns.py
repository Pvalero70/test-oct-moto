# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning
from lxml import etree

### notas de credito en contabilidad
_logger = logging.getLogger(__name__)


class StockPickingReturn(models.Model):
    _inherit = 'stock.picking'

    permiso_devolucion = fields.Boolean(string="Permiso devolucion", compute="_compute_devolucion_permiso", store=False)


    @api.onchange('picking_type_id')
    def _compute_devolucion_permiso(self):
        grupo_devolucion = self.env.user.has_group('credit_note_restrict.aprobe_devolucion_group')
        grupo_recepcion = self.env.user.has_group('credit_note_restrict.aprobe_devolucion_compra_group')
        if self.picking_type_id and self.picking_type_id.sequence_code =='DEV':
            if grupo_devolucion:
                self.permiso_devolucion = True
            else:
                self.permiso_devolucion = False
        elif self.picking_type_id and self.picking_type_id.sequence_code =='IN':
            if grupo_recepcion:
                self.permiso_devolucion=True
            else:
                self.permiso_devolucion = False
        else:
            self.permiso_devolucion = True
        _logger.info("STOCK.PICKING::Computamos permiso dev %s",self.permiso_devolucion)



    def button_solicitar_devolucion(self):
        _logger.info("STOCK.PICKING:: My boton solicitar dev")


