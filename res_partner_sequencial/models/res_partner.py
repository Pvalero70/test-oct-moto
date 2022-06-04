# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning
from lxml import etree

_logger = logging.getLogger(__name__)


class ResPartnertInherit(models.Model):
    _inherit = 'res.partner'

    def _default_seq_code(self):
        seq = ''
        if self.supplier_rank > 0: #Es un proveedor
            seq = self.env['ir.sequence'].next_by_code('res.partner.proveedor.sequence')

        if self.customer_rank > 0: #es un cliente
            seq = self.env['ir.sequence'].next_by_code('res.partner.cliente.sequence')
        return seq

    sequencial_code = fields.Char(string="Numero Contacto", readonly=True, required=True, default=_default_seq_code)



