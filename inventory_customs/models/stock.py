# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


class StockMoveLineC(models.Model):
    _inherit = "stock.move.line"

    motor_number = fields.Char(string="Número de motor")