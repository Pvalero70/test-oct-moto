# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning
from lxml import etree

_logger = logging.getLogger(__name__)


class ResPartnertInherit(models.Model):
    _inherit = 'res.partner'

    def _default_seq_code(self):
        for rec in self:
            seq = ""
            if rec.supplier_rank > 0: #Es un proveedor
                seq = rec.env['ir.sequence'].next_by_code('res.partner.proveedor.sequence')

            if rec.customer_rank > 0: #es un cliente
                seq = rec.env['ir.sequence'].next_by_code('res.partner.cliente.sequence')
            _logger.info("Sequencial = %s",seq)
            rec.sequencial_code_z = seq


    sequencial_code_z = fields.Char(string="Numero Contacto", readonly=True, required=True, compute='_default_seq_code',store=True)


