# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning
from lxml import etree

_logger = logging.getLogger(__name__)

class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    @api.model_create_multi
    def create(self, vals):
        user = super(ResCompanyInherit, self).create(vals)
        if user.partner_id:
            user.partner_id.is_partner_company = True
        return user


class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals):
        user = super(ResUsersInherit, self).create(vals)
        if user.partner_id:
            user.partner_id.is_partner_user = True
        return user


class ResPartnertInherit(models.Model):
    _inherit = 'res.partner'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):

        args = args or []
        domain = []
        if name:
            domain = ['|','|', ('sequencial_code_prov', operator, name), ('sequencial_code_client', operator, name),('name',operator,name)]

        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    def seq_code_prov(self):
        if self.company_id and self.supplier_rank > 0:
            res_partner = self.env['res.partner'].search(
                [('company_id', '=', self.company_id.id), ('supplier_rank', '>', 0)])
            if self.id:
                res_partner = self.env['res.partner'].search(
                    [('company_id', '=', self.company_id.id), ('id', '!=', self.id), ('supplier_rank', '>', 0)])
            arr = [int(contac.sequencial_code_prov) for contac in res_partner]

            if len(res_partner) == 0:
                self.sequencial_code_prov = str(1).zfill(3)
            else:
                max_val = max(arr)

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
                    [('company_id', '=', self.company_id.id), ('id', '!=', self.id), ('customer_rank', '>', 0)])

            arr = [int(contac.sequencial_code_client) for contac in res_partner]

            if len(res_partner) == 0:
                self.sequencial_code_client = str(1).zfill(3)
            else:
                max_val = max(arr)

                self.sequencial_code_client = str(int(max_val) + 1).zfill(3)

    def _default_seq_code_client(self):
        for rec in self:
            rec.seq_code_client()

    is_partner_user = fields.Boolean(string="Es partner de un usuario", compute='_get_user_partner', store=True)
    is_partner_company = fields.Boolean(string="Es partner de una company", compute='_get_company_partner', store=True)

    @api.depends('is_partner_user')
    def _get_user_partner(self):
        for rec in self:
            res_user = rec.env['res.users'].search([('partner_id', '=', rec.id)], limit=1)
            if len(res_user) == 1:
                rec.is_partner_user = True
            else:
                rec.is_partner_user = False

    @api.depends('is_partner_company')
    def _get_company_partner(self):
        for rec in self:
            company_part = rec.env['res.company'].search([('partner_id', '=', rec.id)], limit=1)
            if len(company_part) == 1:
                rec.is_partner_company = True
            else:
                rec.is_partner_company = False

    sequencial_code_prov = fields.Char(string="Numero de Cliente", compute='_default_seq_code_prov', store=True)
    sequencial_code_client = fields.Char(string="Numero de Proveedor", compute='_default_seq_code_client', store=True)

    @api.onchange('company_id')
    def _compute_sequential(self):
        self.seq_code_prov()
        self.seq_code_client()
