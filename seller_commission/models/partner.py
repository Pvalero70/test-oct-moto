# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import logging

_log = logging.getLogger("--__--__-->>> Account Move:: ")

class ResPartnerCommission(models.Model):
    _inherit = "res.partner"

    forze_commission_rule_id = fields.Many2one('seller.commission.rule', "Regla de comisión R&A")