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
            if rec.id and rec.company_id:

                res_partner = rec.env['res.partner'].search(
                    [('company_id', '=', rec.company_id.id), ('id', '!=', rec.id), ('supplier_rank', '>', 0)])
                arr = [contac.sequencial_code_prov for contac in res_partner]

                _logger.info("Res Partner Prov::Valores encontrados = %s, array valores = %s,company activa = %s ",
                             res_partner, arr, rec.company_id.name)
                if len(res_partner) == 0:
                    rec.sequencial_code_prov = str(1).zfill(3)
                else:
                    max_val = max(arr)
                    _logger.info("Res Partner Prov::Valor maximo = %s", max_val)
                    rec.sequencial_code_prov = str(int(max_val) + 1).zfill(3)



    @api.onchange('company_id')
    def _default_seq_code_client(self):
        for rec in self:
            if rec.id and rec.company_id:

                res_partner = rec.env['res.partner'].search(
                    [('company_id', '=', rec.company_id.id), ('id', '!=', rec.id),('customer_rank','>',0)])
                arr = [contac.sequencial_code_client for contac in res_partner]

                _logger.info("Res Partner::Valores encontrados = %s, array valores = %s,company activa = %s ",
                             res_partner, arr, rec.company_id.name)
                if len(res_partner) == 0:
                    rec.sequencial_code_client = str(1).zfill(3)
                else:
                    max_val = max(arr)
                    _logger.info("Res Partner::Valor maximo = %s", max_val)
                    rec.sequencial_code_client = str(int(max_val) + 1).zfill(3)




    sequencial_code_prov = fields.Char(string="Numero de Cliente", readonly=True, compute='_default_seq_code_prov',store=True)
    sequencial_code_client = fields.Char(string="Numero de Proveedor", readonly=True, compute='_default_seq_code_client',store=True)


