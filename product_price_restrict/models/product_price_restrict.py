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
    edit_coste = fields.Boolean("Editar precio de venta", compute='_compute_group_coste', store=False)

    edit_price_sale = fields.Boolean("Grupo sale", default=lambda self: self.env.user.has_group(
        'product_price_restrict.product_sale_price_group'))
    @api.onchange("list_price")
    def _onchangeprice(self):
        if not self.env.user.has_group('product_price_restrict.product_sale_price_group'):
            raise ValidationError(_("Advertencia, no puedes modificar el precio de venta"))

    @api.onchange("standard_price")
    def _onchangeprice(self):
        if not self.env.user.has_group('product_price_restrict.product_price_restrict.product_price_group'):
            raise ValidationError(_("Advertencia, no puedes modificar el coste"))

    """ 
    @api.onchange('name')
    def _compute_group_edit_sale_price(self):
        self.edit_price_sale = self.env.user.has_group('product_price_restrict.product_sale_price_group')
        _log.info("PRODUCT:: Grupo sale permiso %s", self.edit_price_sale)

    @api.onchange('name')
    def _compute_group_coste(self):
        self.edit_coste = self.env.user.has_group('product_price_restrict.product_price_group')
        _log.info("PRODUCT:: Grupo coste permiso %s", self.edit_coste)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(PosOrderC, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                              toolbar=toolbar, submenu=submenu)



        doc = etree.XML(res['arch'])
        _log.info("Calculamos las vistas")
        if view_type =='form':
            if not self.env.user.has_group('product_price_restrict.product_sale_price_group'):
                _log.info("Grupo sale %s, grupo coste %s",self.env.user.has_group('product_price_restrict.product_sale_price_group'), self.env.user.has_group('product_price_restrict.product_price_group'))
                for node_form in doc.xpath("//field[@name='list_price']"):
                    _log.info("Ponemos readonly")
                    node_form.set("readonly", '1')
            if not self.env.user.has_group('product_price_restrict.product_price_group'):
                for node_form in doc.xpath("//field[@name='standard_price']"):
                    node_form.set("readonly", '1')


        res['arch'] = etree.tostring(doc)
        return res
        """
