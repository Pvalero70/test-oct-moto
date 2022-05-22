# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


class PosOrderC(models.Model):
    _inherit = "product.template"


    edit_price_sale = fields.Boolean("Editar precio de venta", compute='_compute_group_edit_sale_price', store=False)
    edit_coste = fields.Boolean("Editar precio de venta", compute='_compute_group_coste',store=False)

    @api.depends('name')
    def _compute_group_edit_sale_price(self):
        self.edit_price_sale = self.env.user.has_group('product_price_restrict.product_sale_price_group')
        _log.info("PRODUCT:: Grupo sale permiso %s", self.edit_price_sale)

    @api.depends('name')
    def _compute_group_coste(self):
        self.edit_coste = self.env.user.has_group('product_price_restrict.product_price_group')
        _log.info("PRODUCT:: Grupo coste permiso %s", self.edit_coste)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(PosOrderC, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                              toolbar=toolbar, submenu=submenu)
        _log.info("PRODUCT:: Recalculamnos permisos")
        self._compute_group_edit_sale_price()
        self._compute_group_coste()

        return res
