import logging
from collections import defaultdict


from odoo import _, api, Command, fields, models
from lxml import etree

_logger = logging.getLogger(__name__)


class ResPartnerName(models.Model):
    _inherit = 'res.partner'

    first_name = fields.Char(string="Primer nombre")
    second_name = fields.Char(string="Segundo nombre")
    first_ap = fields.Char(string="Primer Apellido")
    second_ap = fields.Char(string="Segundo Apellido")


