# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


class AccountMoveCustoms(models.Model):
    _inherit = "account.move"

    