# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError,Warning


_logger = logging.getLogger(__name__)


class ResUserInheritDiscount(models.Model):
    _inherit = 'res.users'

    discount_ids = fields.One2many('res.users.discount', 'seller_id')


class ResUsersDiscount(models.Model):
    _name = 'res.users.discount'

    _description = "Model that saves discounts on product categories"

    seller_id = fields.Many2one('res.users', 'Vendedor', )
    discount_permitted = fields.Integer('Descuento permitido')
    category_ids = fields.Many2many(comodel_name='product.category', string='Categorias')
    almacen_id = fields.Many2one(comodel_name='stock.warehouse', string="Almacen")

    def _restrictions_discounts(self, seller, discount_permitted,almacen_id):
        descuento_20 = self.env.user.has_group('pos_user_restrict.user_discount_gerente_group')

        _logger.info('resultado pertenece a  grupo : %s : y vendedor %s', descuento_20, seller, )
        if descuento_20 == True and self.env.user.property_warehouse_id.id != almacen_id and discount_permitted<=20 and discount_permitted>5:
            almacen = self.env['stock.warehouse'].search([('id', '=', almacen_id)], limit=1)
            raise ValidationError(_('Advertencia!, No tienes permiso de gerente para el almacen %s.',almacen.name))

        if discount_permitted > 5 and descuento_20 == False:
            raise ValidationError(_('Advertencia!, El descuento maximo permitido es 5%.'))

        if discount_permitted > 20 and descuento_20 == True:
            raise ValidationError(_('Advertencia!, El descuento maximo permitido es 20%.'))

        if discount_permitted > 20 and descuento_20 == False:
            raise ValidationError(_('Advertencia!, El descuento maximo permitido es 5%.'))

    def _verificar_duplicados(self,categorias_ids,descuentos_lines,almacen_id):
        for j in range(len(categorias_ids)):
            for k in range(len(descuentos_lines)):
                _logger.info('Categoriass id = %s', categorias_ids[j])
                _logger.info('Antes del for %s', descuentos_lines[k].category_ids)
                if categorias_ids[j] in [cat.id for cat in descuentos_lines[k].category_ids] and almacen_id == descuentos_lines[k].almacen_id.id:
                    categoria_rep = self.env['product.category'].search([('id', '=', categorias_ids[j])], limit=1)
                    raise ValidationError(
                        _('Advertencia!, Ya existe otro descuento con la categoria %s y almacen %s ',
                          categoria_rep.name, descuentos_lines[k].almacen_id.name))

    def write(self, vals):
        _logger.info('Write Method a %s with vals %s', self._name, vals)

        seller = self.seller_id
        discount_permitted = self.discount_permitted
        almacen_id = self.almacen_id.id
        if 'discount_permitted' in vals:
            discount_permitted = vals['discount_permitted']

        if 'seller_id' in vals:
            seller = self.env['res.users'].search([('id', '=', vals['seller_id'])], limit=1)
        if 'almacen_id' in vals:
            almacen_id = vals['almacen_id']

        self._restrictions_discounts(seller, discount_permitted,almacen_id)

        if 'category_ids' in vals:
            lis_category_ids = vals['category_ids'][0][2]
            descuentos_lines = self.env['res.users.discount'].search([('seller_id', '=', seller.id),('id','!=',self.id)])
            self._verificar_duplicados(lis_category_ids,descuentos_lines,almacen_id)

        return super(ResUsersDiscount, self).write(vals)

    @api.model_create_multi
    def create(self, vals):
        _logger.info('Create a %s with vals %s', self._name, vals)
        # descuento_20 = self.env.user.has_group('pos_user_restrict.user_discount_agente_group')
        # grupos = self.env.user.groups_id
        for i in range(len(vals)):
            seller = self.env['res.users'].search([('id', '=', vals[i]['seller_id'])], limit=1)
            permitted_discount = vals[i]['discount_permitted']
            almacen_id = vals[i]['almacen_id']

            self._restrictions_discounts(seller, permitted_discount,almacen_id)

            categorias_ids = vals[i]['category_ids'][0][2]
            _logger.info('Categorys id = %s', categorias_ids)
            descuentos_lines = self.env['res.users.discount'].search([('seller_id', '=', vals[i]['seller_id'])])

            self._verificar_duplicados(categorias_ids,descuentos_lines,vals['almacen_id'])

        return super(ResUsersDiscount, self).create(vals)


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    need_discount_aprove = fields.Boolean("Nesesita descuento mayor?",default=False)

    def send_mail_discount(self):
        _logger.info("SALE ORDER: Boton solicitar descuento")
        if not self.env.user.property_warehouse_id:
            raise ValidationError(_('Advertencia!, No tienes almacen predeterminado seleccionado'))
        almacen = self.env.user.property_warehouse_id
        list_usuarios = self.env['res.users'].search([('property_warehouse_id', '=', almacen.id)])
        for usuario in list_usuarios:
            if usuario.has_group('pos_user_restrict.user_discount_gerente_group'):
                descuentos_requeridos = self._get_category_needs_discount()

                _logger.info("SALE ORDER: Boton email , descuentos solicitados= %s",descuentos_requeridos)
                if len(descuentos_requeridos)>0:

                    body = 'El usuario '+self.env.user.name+' en la cotizacion '+ self.name+' solicita descuentos para las categorias:<br>'
                    for desc_req in descuentos_requeridos:
                        body += "Categoria : "+str(desc_req['categoria'])+" con un valor de " + str(desc_req['descuento_solicitado'])+"%.<br>"
                    template_obj = self.env['mail.mail']
                    template_data = {
                        'subject': 'Solicitud de descuento para' + self.env.user.name,
                        'body_html': body,
                        'email_from': self.env.user.company_id.email,
                        'email_to': usuario.partner_id.email
                    }
                    _logger.info("SALE ORDER: Enviamos email con %s",template_data)
                    template_id = template_obj.create(template_data)
                    template_id.send()
                    _logger.info("SALE ORDER: Enviado")

        return True


    def _get_category_needs_discount(self):
        discount_lines = self.env['res.users.discount'].search(
            [('seller_id', '=', self.env.user.id), ('almacen_id', '=', self.warehouse_id.id)], limit=1)
        _logger.info("SALE ORDER:: cantidad de registros %s,valores %s", len(discount_lines), discount_lines)
        descuentos_sol = []
        for order in self.order_line:

            if order.product_template_id and order.product_template_id.categ_id:
                _logger.info("SALE ORDER:: Linea con valores %s, y categoria %s, descuento %s",
                             order.product_template_id.name,
                             order.product_template_id.categ_id.name, order.discount)
                if len(discount_lines) > 0:
                    for discount_line in discount_lines:
                        _logger.info("SALE ORDER:: Linea Descuento con valores %s, y categoria %s",
                                     discount_line.discount_permitted, [cat.name for cat in discount_line.category_ids])
                        for categ in discount_line.category_ids:

                            if categ.id == order.product_template_id.categ_id.id:
                                if order.discount > discount_line.discount_permitted:

                                    descuentos_sol.append({'categoria':categ.name,'descuento_solicitado':order.discount})

        return descuentos_sol

    def restrictions_discount(self):
        discount_lines = self.env['res.users.discount'].search([('seller_id', '=', self.env.user.id),('almacen_id','=',self.warehouse_id.id)], limit=1)
        _logger.info("SALE ORDER:: cantidad de registros %s,valores %s",len(discount_lines),discount_lines)
        descuentos_mayores = False
        errores_string = ''
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

                            if categ.id == order.product_template_id.categ_id.id :
                                descuento_encontrado=1
                                if order.discount > discount_line.discount_permitted:
                                    descuentos_mayores = True

                                    errores_string += 'Advertencia!, El descuento permitido en %s para categoria %s es %s\n.'% (order.product_template_id.name,categ.name, discount_line.discount_permitted)

                    if descuento_encontrado == 0 and order.discount > 0:
                        errores_string += 'Advertencia!, No tienes permitido hacer descuentos en %s'%(
                                             order.product_template_id.categ_id.name)
                    _logger.info('SALE ORDER:: descuento encontrado: %s',descuento_encontrado)

                else:
                    if order.discount>0:
                        errores_string += 'Advertencia!, No tienes permitido hacer descuentos en categoria %s\n' %(order.product_template_id.categ_id.name)


        if descuentos_mayores == True:
            self.need_discount_aprove = True
        else:
            self.need_discount_aprove = False
        self.sudo().write({'need_discount_aprove':descuentos_mayores})
        _logger.info("SALE ORDER: errores %s , len %s",errores_string, len(errores_string))
        _logger.info("SALE ORDER:: Valor need aprove: %s", descuentos_mayores)
        if len(errores_string)>0:
            raise UserError(errores_string)

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


