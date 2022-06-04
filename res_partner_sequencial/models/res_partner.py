# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning
from lxml import etree

_logger = logging.getLogger(__name__)


class ResPartnertInherit(models.Model):
    _inherit = 'res.partner'

    @api.onchange('supplier_rank','customer_rank')
    def _default_seq_code(self):
        for rec in self:
            seq = ""
            if rec.supplier_rank > 0: #Es un proveedor
                seq = rec.env['ir.sequence'].next_by_code('res.partner.proveedor.sequence')
                rec.sequencial_code_prov = seq
                _logger.info("Proveedor Sequencial = %s", seq)

            if rec.customer_rank > 0: #es un cliente
                seq = rec.env['ir.sequence'].next_by_code('res.partner.cliente.sequence')
                rec.sequencial_code_client = seq
                _logger.info("Cliente Sequencial = %s", seq)




    sequencial_code_prov = fields.Char(string="Sequencial Cliente", readonly=True, required=True, compute='_default_seq_code',store=True)
    sequencial_code_client = fields.Char(string="Sequencial Proveedor", readonly=True, required=True, compute='_default_seq_code',store=True)


