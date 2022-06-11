# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning
from lxml import etree

_log = logging.getLogger("___name: %s" % __name__)

from lxml import etree


            
class PosOrderC(models.Model):
    _inherit = "product.template"

    # edit_price_sale = fields.Boolean("Editar precio de venta", compute='_compute_group_edit_sale_price', store=False)

    list_price_permited = fields.Boolean(string="Readonly para el campo discount",readonly=False, compute='get_user_list_price')
    standard_price_permited = fields.Boolean(string="Readonly para el campo discount",readonly=False, compute='get_user_standard_price')

    @api.depends('list_price_permited')
    def get_user_list_price(self):
        _log.info("Aqui 1")
        res_user = self.env.user
        if res_user.has_group('product_price_restrict.product_sale_price_group'):
            self.list_price_permited = True
        else:
            self.list_price_permited = False

    @api.depends('standard_price_permited')
    def get_user_standard_price(self):
        res_user = self.env.user
        if res_user.has_group('product_price_restrict.product_price_group'):
            self.standard_price_permited = True
        else:
            self.standard_price_permited = False




