# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


_logger = logging.getLogger(__name__)

class ResUserInheritDiscount(models.Model):
    _inherit = 'res.users'

    discount_ids = fields.One2many('res.users.discount','seller_id',String="Lista de Descuentos")


class ResUsersDiscount(models.Model):
    _name = 'res.users.discount'

    _description = "Model that saves discounts on product categories"

    seller_id = fields.Many2one('res.users' , 'Vendedor',)
    discount_permitted = fields.Integer('Descuento permitido')
    category_ids = fields.Many2many(comodel_name='product.category' , string='Categorias')


    def write(self, values):
        _logger.info('Create a %s with vals %s', self._name, values)
        res = self.env.user.has_group('pos_user_restrict.user_discount_agente_group')
        grupos = self.env.user.groups_id
        _logger.info('resultado de grupo : %s : y grupos : %s', res, grupos)
        return super(ResUsersDiscount, self).write(values)

    @api.model_create_multi
    def create(self, vals):
        _logger.info('Create a %s with vals %s', self._name, vals)
        descuento_20 = self.env.user.has_group('pos_user_restrict.user_discount_agente_group')

        grupos = self.env.user.groups_id
        seller = vals['seller_id'].has_group('pos_user_restrict.user_discount_agente_group')
        _logger.info('resultado de grupo : %s : y grupos : %s : y vendedor %s', descuento_20, grupos,seller)

        if vals['discount_permitted']>5 and descuento_20 == False:
            raise ValidationError(_('Advertencia!, El descuento maximo permitido es 5%.'))

        if vals['discount_permitted']>20 and descuento_20 == True:
            raise ValidationError(_('Advertencia!, El descuento maximo permitido es 20%.'))

        return super(ResUsersDiscount, self).create(vals)




