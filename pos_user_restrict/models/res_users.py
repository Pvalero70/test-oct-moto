# -*- coding: utf-8 -*-

from odoo import fields, models


import logging

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    pos_config_ids = fields.Many2many(
        comodel_name='pos.config',
        string='POS permitidos',
        help="Allowed Points of Sales for the user. POS managers can use all POS.",
    )

    def write(self, values):
        res = super(ResUsers, self).write(values)
        if self.ids and 'pos_config_ids' in values:
            self.env['ir.model.access'].call_cache_clearing_methods()
            self.env['ir.rule'].clear_caches()

            try:
                self.has_group.clear_cache(self)
            except Exception as e:
                _logger.error(e)
        return res
