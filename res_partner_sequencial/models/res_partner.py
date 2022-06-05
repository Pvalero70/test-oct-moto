# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning
from lxml import etree

_logger = logging.getLogger(__name__)


class ResPartnertInherit(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        _logger.info("RES PARTNER SEARCH FUNC")
        args = args or []

        if not (name == '' and operator == 'ilike'):
            args += ['|', ('sequencial_code_prov', 'ilike', name),('sequencial_code_client', 'ilike', name)]
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)



    def seq_code_prov(self):
        if self.company_id and self.supplier_rank > 0:
            res_partner = self.env['res.partner'].search(
                [('company_id', '=', self.company_id.id), ('supplier_rank', '>', 0)])
            if self.id:
                res_partner = self.env['res.partner'].search(
                    [('company_id', '=', self.company_id.id), ('id','!=',self.id), ('supplier_rank', '>', 0)])
            arr = [int(contac.sequencial_code_prov) for contac in res_partner]

            _logger.info("Res Partner Prov::Valores encontrados = %s, array valores = %s,company activa = %s ",
                         res_partner, arr, self.company_id.name)
            if len(res_partner) == 0:
                self.sequencial_code_prov = str(1).zfill(3)
            else:
                max_val = max(arr)
                _logger.info("Res Partner Prov::Valor maximo = %s", max_val)
                self.sequencial_code_prov = str(int(max_val) + 1).zfill(3)

    def _default_seq_code_prov(self):
        for rec in self:
            rec.seq_code_prov()

    def seq_code_client(self):
        if self.company_id and self.customer_rank > 0:

            res_partner = self.env['res.partner'].search(
                [('company_id', '=', self.company_id.id), ('customer_rank', '>', 0)])
            if self.id:
                res_partner = self.env['res.partner'].search(
                    [('company_id', '=', self.company_id.id), ('id','!=',self.id), ('customer_rank', '>', 0)])

            arr = [int(contac.sequencial_code_client) for contac in res_partner]

            _logger.info("Res Partner::Valores encontrados = %s, array valores = %s,company activa = %s ",
                         res_partner, arr, self.company_id.name)
            if len(res_partner) == 0:
                self.sequencial_code_client = str(1).zfill(3)
            else:
                max_val = max(arr)
                _logger.info("Res Partner::Valor maximo = %s", max_val)
                self.sequencial_code_client = str(int(max_val) + 1).zfill(3)

    def _default_seq_code_client(self):
        for rec in self:
            rec.seq_code_client()

    is_partner_user = fields.Boolean(string="Es partner de un usuario", compute='_get_user_partner')

    @api.depends('is_partner_user')
    def _get_user_partner(self):

        if self.id:
            res_user = self.env['res.users'].search([('partner_id', '=', self.id)],limit=1)
            if len(res_user) == 1:
                self.is_partner_user = True
            else:
                self.is_partner_user = False
            _logger.info("Is partner User: %s",self.is_partner_user)

    sequencial_code_prov = fields.Char(string="Numero de Cliente", compute='_default_seq_code_prov',store=True)
    sequencial_code_client = fields.Char(string="Numero de Proveedor", compute='_default_seq_code_client',store=True)



    @api.onchange('company_id')
    def _compute_sequential(self):
        _logger.info('Res Partner:: Cambio la company')
        self.seq_code_prov()
        self.seq_code_client()

