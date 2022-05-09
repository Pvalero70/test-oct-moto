# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import logging
_log = logging.getLogger("___name: %s" % __name__)


class ProductProductBc(models.Model):
    _inherit = "product.product"

    package_carrier_type = fields.Selection(selection_add=[('dhl', 'DHL')])