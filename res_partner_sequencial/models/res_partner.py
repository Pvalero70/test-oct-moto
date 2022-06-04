# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning
from lxml import etree

_logger = logging.getLogger(__name__)


class ResPartnertInherit(models.Model):
    _inherit = 'res.partner'

    @api.onchange('supplier_rank','company_id')
    def _default_seq_code_prov(self):
        for rec in self:
            if rec.supplier_rank > 0 and rec.company_id: #Es un proveedor
                context = {}
                context['force_company'] = rec.company_id.id
                seq = rec.env['ir.sequence'].next_by_code('res.partner.proveedor.sequence',context=context)
                rec.sequencial_code_prov = seq
                _logger.info("Proveedor Sequencial = %s", seq)



    @api.onchange('customer_rank','company_id')
    def _default_seq_code_client(self):
        for rec in self:
            if rec.customer_rank > 0 and rec.company_id:  # es un cliente
                context = {}
                context['force_company'] = rec.company_id.id
                seq = rec.env['ir.sequence'].next_by_code('res.partner.cliente.sequence',context=context)
                rec.sequencial_code_client = seq
                _logger.info("Cliente Sequencial = %s", seq)




    sequencial_code_prov = fields.Char(string="Numero de Cliente", readonly=True, compute='_default_seq_code_prov',store=True)
    sequencial_code_client = fields.Char(string="Numero de Proveedor", readonly=True, compute='_default_seq_code_client',store=True)


