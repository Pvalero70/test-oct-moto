# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning
from lxml import etree

_log = logging.getLogger("___name: %s" % __name__)

from lxml import etree

class ProductSuplierInherit(models.Model):
    _inherit = "product.supplierinfo"

    price_compra_proveedor = fields.Boolean(string="Readonly para el campo precio en proveedores", readonly=False,
                                            compute='get_user_price_proveedor')

    @api.depends('price_compra_proveedor')
    def get_user_price_proveedor(self):
        res_user = self.env.user
        if res_user.has_group('product_price_restrict.product_price_proveedores_group'):
            self.price_compra_proveedor = True
        else:
            self.price_compra_proveedor = False


class ProductProductInherit(models.Model):
    _inherit = "product.product"


    list_price_permited = fields.Boolean(string="Readonly para el campo discount", readonly=False,
                                         compute='get_user_list_price')
    standard_price_permited = fields.Boolean(string="Readonly para el campo discount", readonly=False,
                                             compute='get_user_standard_price')

    @api.depends('list_price_permited')
    def get_user_list_price(self):
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


class ProductTemplateInherit(models.Model):
    _inherit = "product.template"


    list_price_permited = fields.Boolean(string="Readonly para el campo discount",readonly=False, compute='get_user_list_price')
    standard_price_permited = fields.Boolean(string="Readonly para el campo discount",readonly=False, compute='get_user_standard_price')

    @api.depends('list_price_permited')
    def get_user_list_price(self):

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




