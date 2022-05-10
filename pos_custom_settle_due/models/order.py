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

    @api.model
    def create_from_ui(self, orders, draft=False):
        _logger.info("## SOBRE ESCRIBE CREAR ORDEN ##")
        _logger.info(orders)
        _logger.info(draft)
        res = super(PosOrder, self).create_from_ui(orders, draft)
        _logger.info(res)
        return res