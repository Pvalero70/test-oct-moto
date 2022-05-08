# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import logging
_log = logging.getLogger("___name: %s" % __name__)


class ResCompanyTt(models.Model):
    _inherit = "res.company"

    restrict_inv_sn_flow = fields.Boolean(string="Restringir Flujo SN",
                                          default=False,
                                          help="Restringe el flujo de número de serie especifico para motocicletas.")