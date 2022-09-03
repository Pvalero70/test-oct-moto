# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

from datetime import datetime

import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
	_inherit = "sale.order"

