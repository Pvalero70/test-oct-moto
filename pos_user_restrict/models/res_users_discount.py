# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class ResUserInheritDiscount(models.Model):
    _inherit = 'res.users'

    discount_ids = fields.One2many('res.users.discount', 'seller_id', String="Lista de Descuentos")


class ResUsersDiscount(models.Model):
    _name = 'res.users.discount'

    _description = "Model that saves discounts on product categories"

    seller_id = fields.Many2one('res.users', 'Vendedor', )
    discount_permitted = fields.Integer('Descuento permitido')
    category_ids = fields.Many2many(comodel_name='product.category', string='Categorias')
    location_ids = fields.Many2many(comodel_name='stock.location', string="Ubicacion")

    def _restrictions_discounts(self, seller, discount_permitted):
        descuento_20 = seller.has_group('pos_user_restrict.user_discount_agente_group')
        _logger.info('resultado pertenece a  grupo : %s : y vendedor %s', descuento_20, seller, )

        if discount_permitted > 5 and descuento_20 == False:
            raise ValidationError(_('Advertencia!, El descuento maximo permitido es 5%.'))

        if discount_permitted > 20 and descuento_20 == True:
            raise ValidationError(_('Advertencia!, El descuento maximo permitido es 20%.'))

        if discount_permitted > 20 and descuento_20 == False:
            raise ValidationError(_('Advertencia!, El descuento maximo permitido es 5%.'))

    def write(self, vals):
        _logger.info('Write Method a %s with vals %s', self._name, vals)
        descuento_20 = self.seller_id.has_group('pos_user_restrict.user_discount_agente_group')

        _logger.info('permiso 20% ', descuento_20)
        seller = self.seller_id
        discount_permitted = self.discount_permitted
        if 'discount_permitted' in vals:
            discount_permitted = vals['discount_permitted']

        if 'seller_id' in vals:
            seller = self.env['res.users'].search([('id', '=', vals['seller_id'])], limit=1)

        self._restrictions_discounts(seller, discount_permitted)

        if 'category_ids' in vals:
            lis_category_ids = vals['category_ids'][0][2]
            descuentos_lines = self.env['res.users.discount'].search([('seller_id', '=', seller.id)])

        return super(ResUsersDiscount, self).write(vals)

    @api.model_create_multi
    def create(self, vals):
        _logger.info('Create a %s with vals %s', self._name, vals)
        # descuento_20 = self.env.user.has_group('pos_user_restrict.user_discount_agente_group')
        # grupos = self.env.user.groups_id
        for i in range(len(vals)):
            seller = self.env['res.users'].search([('id', '=', vals[i]['seller_id'])], limit=1)
            permitted_discount = vals[i]['discount_permitted']

            self._restrictions_discounts(seller, permitted_discount)

            categorias_ids = vals[i]['category_ids'][0][2]
            _logger.info('Categorys id = %s', categorias_ids)
            descuentos_lines = self.env['res.users.discount'].search([('seller_id', '=', vals[i]['seller_id'])])
            for j in range(len(categorias_ids)):
                for k in range(len(descuentos_lines)):
                    _logger.info('Categoriass id = %s', categorias_ids[j])
                    _logger.info('Antes del for %s', descuentos_lines[k].category_ids)
                    if categorias_ids[j] in [cat.id for cat in descuentos_lines[k].category_ids]:
                        categoria_rep = self.env['product.category'].search([('id', '=', categorias_ids[j])], limit=1)
                        raise ValidationError(
                            _('Advertencia!, La categoria %s ya esta en otro registro', categoria_rep.name))

        return super(ResUsersDiscount, self).create(vals)


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'





    def restrictions_discount(self):
        discount_lines = self.env['res.users.discount'].search([('seller_id', '=', self.env.user.id)], limit=1)
        _logger.info("SALE ORDER:: cantidad de registros %s,valores %s",len(discount_lines),discount_lines)

        for order in self.order_line:
            descuento_encontrado=0
            if order.product_template_id and order.product_template_id.categ_id:
                _logger.info("SALE ORDER:: Linea con valores %s, y categoria %s, descuento %s", order.product_template_id.name,
                             order.product_template_id.categ_id.name,order.discount)
                if len(discount_lines)>0:
                    for discount_line in discount_lines:
                        _logger.info("SALE ORDER:: Linea Descuento con valores %s, y categoria %s",
                                     discount_line.discount_permitted,[cat.name for cat in discount_line.category_ids])
                        for categ in discount_line.category_ids:

                            if categ.id == order.product_template_id.categ_id.id:
                                descuento_encontrado=1
                                if order.discount > discount_line.discount_permitted:
                                    raise ValidationError(_('Advertencia!, El descuento permitido en %s para categoria %s es %s.',order.product_template_id.name,categ.name, discount_line.discount_permitted))
                    _logger.info('SALE ORDER:: descuento encontrado: %s',descuento_encontrado)
                    if descuento_encontrado == 0:
                        raise ValidationError(_('Advertencia!, No tienes permitido hacer descuentos en %s',order.product_template_id.categ_id.name))
                else:
                    if order.discount>0:
                        raise ValidationError(_('Advertencia!, No tienes permitido hacer descuentos'))

        return True
    def action_confirm(self):
        _logger.info("SALE ORDER::Confirmar accion")
        self.restrictions_discount()

        return False
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write(self._prepare_confirmation_values())

        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        context = self._context.copy()
        context.pop('default_name', None)

        self.with_context(context)._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()
        return True