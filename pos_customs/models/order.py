# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import timedelta
from functools import partial
from itertools import groupby

import psycopg2
import pytz
import re

from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero, float_round, float_repr, float_compare
from odoo.exceptions import ValidationError, UserError
from odoo.http import request
from odoo.osv.expression import AND
import base64

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    # @api.model
    # def create_from_ui(self, orders, draft=False):
        # _logger.info("## SOBRE ESCRIBE CREAR ORDEN ##")
        # _logger.info(orders)
        # res = super(PosOrder, self).create_from_ui(orders, draft)
        # _logger.info(res)
        # return res

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def get_sale_order(self, order):
        _logger.info("orders %s",order)
        _logger.info(order)
        sale_order = self.env['sale.order'].search([('id', '=', order['id'])])
        _logger.info("Sale order encontrada %s",sale_order)
        if sale_order.payment_term_id:
            payment_term = sale_order.payment_term_id
            return [payment_term.id, payment_term.name]
        return False
        