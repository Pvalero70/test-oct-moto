# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class Purchase(models.Model):

    _inherit = "purchase.order"

    import_xml_cfdi = fields.Many2one("pmg.importa.cfdi", string="Cfdi")
