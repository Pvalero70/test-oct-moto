# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


class StockMoveLineC(models.Model):
    _inherit = "stock.move.line"

    is_moto = fields.Boolean(string="Es motocicleta", compute="_compute_is_moto", store=False)
    motor_number = fields.Char(string="Número de motor")

    def _compute_is_moto(self):
        if self.move_id.product_id and self.move_id.product_id.product_inv_categ and self.move_id.product_id.product_inv_categ == "moto":
            _log.info("------ES UNA MOTO-")
            self.is_moto = True
        else:
            _log.info("------- NOOO ES MOTO ")
            self.is_moto = False
