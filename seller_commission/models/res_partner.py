# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class ResPartnerSc(models.Model):
    _inherit = "res.partner"

    commission_ids = fields.Many2many('seller.commission', 'commission_partner_rel', 'comm_id', 'partner_id', string="Comisiones acumuladas")
    commission_unpaid_line_ids = fields.Many2many('seller.commission.line', "commission_line_partner_rel", 'lcom_id', 'lpartner_id', String="Conceptos de comisión sin pagar")