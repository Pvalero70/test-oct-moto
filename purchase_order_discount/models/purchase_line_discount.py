# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning
from lxml import etree

_logger = logging.getLogger(__name__)



class PurchaseOrderLineDiscount(models.Model):
    _inherit = 'purchase.order.line'

    discount = fields.Float('Descuento %')
    discount_permited = fields.Boolean(string="Readonly para el campo discount", compute='get_user')

    @api.model_create_multi
    def create(self, vals):

        res = super(PurchaseOrderLineDiscount, self).create(vals)
        if not self.env.user.has_group('purchase_order_discount.user_discount_purchase_group'):
            res.discount_permited = False
        else:
            res.discount_permited = True
        return res

    @api.onchange('product_id')
    def _compute_discount_permited_create(self):
        _logger.info("Onchange order Line")
        if not self.id:
            if self.env.user.has_group('purchase_order_discount.user_discount_purchase_create_group'):
                _logger.info("Onchange order Line True")
                self.discount_permited = True
                return
        _logger.info("Onchange order Line False")
        self.discount_permited = False



    @api.onchange('discount')
    def _compute_discount_permited(self):

        if self.discount>100 or self.discount<0:
            raise ValidationError(_("El descuento introducido debe ser entre 0 y 100"))

    @api.depends('discount_permited')
    def get_user(self):
        _logger.info("Usuario Calculamos")
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        _logger.info("Usuario %s",res_user.name)
        _logger.info("Tiene grupo %s",res_user.has_group('purchase_order_discount.user_discount_purchase_group'))

        _logger.info("Usuario en self %s", self.env.user.name)
        _logger.info("Tiene grupo en self %s", self.env.user.has_group('purchase_order_discount.user_discount_purchase_group'))

        if res_user.has_group('purchase_order_discount.user_discount_purchase_group'):
            self.discount_permited = True
        else:
            self.discount_permited = False


    @api.depends('product_qty', 'price_unit', 'taxes_id','discount')
    def _compute_amount(self):
        vals = super(PurchaseOrderLineDiscount, self)._compute_amount()
        return vals

    def _prepare_compute_all_values(self):

        # Hook method to returns the different argument values for the
        # compute_all method, due to the fact that discounts mechanism
        # is not implemented yet on the purchase orders.
        # This method should disappear as soon as this feature is
        # also introduced like in the sales module.
        self.ensure_one()
        return {
            'price_unit': self.price_unit - (self.price_unit * (self.discount/100)),
            'currency': self.order_id.currency_id,
            'quantity': self.product_qty,
            'product': self.product_id,
            'partner': self.order_id.partner_id,
        }

    #Modificamos para la creacion de la factura
    def _prepare_account_move_line(self):
        vals = super(PurchaseOrderLineDiscount, self)._prepare_account_move_line()
        vals.update({'discount':self.discount})
        return vals

