# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning

_logger = logging.getLogger(__name__)


class ResUserInheritDiscount(models.Model):
    _inherit = 'res.users'

    discount_ids = fields.One2many('res.users.discount', 'seller_id')


class ResUsersDiscount(models.Model):
    _name = 'res.users.discount'

    _description = "Model that saves discounts on product categories"
    _rec_name = 'name_computed'

    name_computed = fields.Char(string="Computado", compute='_compute_name')
    seller_id = fields.Many2one('res.users', 'Vendedor', )
    discount_permitted = fields.Integer('Descuento permitido')
    category_ids = fields.Many2many(comodel_name='product.category', string='Categorias')
    almacen_id = fields.Many2one(comodel_name='stock.warehouse', string="Almacen")

    @api.depends('seller_id')
    def _compute_name(self):
        for test in self:
            test.name_computed = test.seller_id.name

    def _descuento_motos(self, categorias_ids):
        if not self.env.user.has_group('pos_order_restrict.user_discount_motos_group'):
            for categoria_id in categorias_ids:
                categoria = self.env['product.category'].search([('id', '=', categoria_id)], limit=1)

                if categoria.name == 'Motos':
                    raise UserError(_("No puedes dar descuentos en motos"))
                categ = categoria
                while categ.parent_id:
                    if categ.parent_id.name == 'Motos':
                        raise UserError(_("No puedes dar descuentos en motos"))
                    categ = categ.parent_id

    def _verifica_categoria_motos(self, categorias_ids):

        for categoria_id in categorias_ids:
            categoria = self.env['product.category'].search([('id', '=', categoria_id)], limit=1)
            if categoria.name == 'Motos':
                return True
            categ = categoria
            while categ.parent_id:
                if categ.parent_id.name == 'Motos':
                    return True
                categ = categ.parent_id
        return False

    def _restrictions_discounts(self, seller, discount_permitted, almacen_id, categorias_ids):
        descuento_gerente = self.env.user.has_group('pos_order_restrict.user_discount_gerente_modif_group')
        acceso_motos = self.env.user.has_group('pos_order_restrict.user_discount_motos_group')
        descuento_user_base = seller.company_id.user_base_discount
        descuento_user_gerente = seller.company_id.user_gerentes_discount
        descuento_motos = seller.company_id.motos_discount

        _logger.info("POS ORDER:discount permited %s, Descuento base %s , gerente %s, motos %s, verifica cat motos %s",
                     discount_permitted, descuento_user_base, descuento_user_gerente, descuento_motos,
                     self._verifica_categoria_motos(categorias_ids))
        if acceso_motos == True and self._verifica_categoria_motos(categorias_ids) == True:
            if discount_permitted > descuento_motos:
                raise ValidationError(
                    _('Advertencia!, El descuento maximo permitido para motos es %s.', descuento_motos))
            else:
                return True

        elif descuento_gerente == True and discount_permitted > descuento_user_gerente:
            raise ValidationError(
                _('Advertencia!, El descuento maximo permitido para gerente es %s.', descuento_user_gerente))

        elif descuento_gerente == False and discount_permitted > descuento_user_base:
            raise ValidationError(
                _('Advertencia!, El descuento maximo permitido usuario base es %s ', descuento_user_base))

    def _verificar_duplicados(self, categorias_ids, descuentos_lines, almacen_id):
        for j in range(len(categorias_ids)):
            for k in range(len(descuentos_lines)):

                if categorias_ids[j] in [cat.id for cat in descuentos_lines[k].category_ids] and almacen_id == \
                        descuentos_lines[k].almacen_id.id:
                    categoria_rep = self.env['product.category'].search([('id', '=', categorias_ids[j])], limit=1)
                    raise ValidationError(
                        _('Advertencia!, Ya existe otro descuento con la categoria %s y almacen %s ',
                          categoria_rep.name, descuentos_lines[k].almacen_id.name))

    def write(self, vals):
        seller = self.seller_id
        discount_permitted = self.discount_permitted
        almacen_id = self.almacen_id.id
        category_ids = [cat.id for cat in self.category_ids]
        if 'discount_permitted' in vals:
            discount_permitted = vals['discount_permitted']

        if 'seller_id' in vals:
            seller = self.env['res.users'].search([('id', '=', vals['seller_id'])], limit=1)
        if 'almacen_id' in vals:
            almacen_id = vals['almacen_id']

        if 'category_ids' in vals:
            lis_category_ids = vals['category_ids'][0][2]
            category_ids = lis_category_ids
        _logger.info(_("POS ORDER::Bien"))
        descuentos_lines = self.env['res.users.discount'].search(
            [('seller_id', '=', seller.id), ('id', '!=', self.id)])
        self._descuento_motos(category_ids)
        self._restrictions_discounts(seller, discount_permitted, almacen_id, category_ids)
        self._verificar_duplicados(category_ids, descuentos_lines, almacen_id)

        return super(ResUsersDiscount, self).write(vals)

    @api.model_create_multi
    def create(self, vals):
        for i in range(len(vals)):
            if not 'category_ids' in vals[i]:
                raise ValidationError(_("Advertencia, se debe seleccionar almenos una categoria "))
            seller = self.env['res.users'].search([('id', '=', vals[i]['seller_id'])], limit=1)
            permitted_discount = vals[i]['discount_permitted']
            almacen_id = vals[i]['almacen_id']
            categorias_ids = vals[i]['category_ids'][0][2]

            self._restrictions_discounts(seller, permitted_discount, almacen_id, categorias_ids)

            descuentos_lines = self.env['res.users.discount'].search([('seller_id', '=', vals[i]['seller_id'])])

            self._verificar_duplicados(categorias_ids, descuentos_lines, vals[i]['almacen_id'])
            self._descuento_motos(categorias_ids)

        return super(ResUsersDiscount, self).create(vals)


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    need_discount_aprove = fields.Boolean("Nesesita descuento mayor?", compute='_get_value', store=True)


    gerente_discount_id = fields.Many2one('res.users', "Gerente a cargo de aprobar")

    @api.depends('order_line')
    def _get_value(self):
        list = self._get_category_needs_discount()
        if len(list):
            self.need_discount_aprove = True

            self.gerente_discount_id = False
        else:
            self.need_discount_aprove = False

    def send_mail_discount(self):

        if not self.warehouse_id:
            raise ValidationError(_('Advertencia!, No tienes almacen seleccionado'))
        almacen = self.warehouse_id
        list_usuarios = self.env['res.users'].search([('property_warehouse_id', '=', almacen.id)])
        _logger.info("Usuarios con almacen predeterminado = %s", list_usuarios)

        gerente_encontrado = 0
        for usuario in list_usuarios:
            _logger.info("SALE ORDER:: usuario %s , tiene grupo %s", usuario.name,
                         usuario.has_group('pos_order_restrict.user_discount_gerente_group'))
            if usuario.has_group('pos_order_restrict.user_discount_gerente_group'):
                descuentos_requeridos = self._get_category_needs_discount()
                gerente_encontrado = 1
                self.gerente_discount_id = usuario
                _logger.info("SALE ORDER: Boton email , descuentos solicitados= %s", descuentos_requeridos)
                if len(descuentos_requeridos) > 0:

                    body = 'El usuario ' + self.env.user.name + ' en la cotizacion ' + self.name + ' solicita descuentos para las categorias:<br>'
                    for desc_req in descuentos_requeridos:
                        body += "En el producto " + str(desc_req['producto']) + " con la categoria : " + str(
                            desc_req['categoria']) + " se pide un descuento mayor de " + str(desc_req[
                                                                                                 'descuento_solicitado']) + "%. El usuario cuenta con un descuento maximo de el " + str(
                            desc_req['descuento_permitido']) + "%<br>"
                    template_obj = self.env['mail.mail']
                    template_data = {
                        'subject': 'Solicitud de descuento para' + self.env.user.name,
                        'body_html': body,
                        'email_from': self.env.user.company_id.email,
                        'email_to': usuario.partner_id.email
                    }
                    _logger.info("SALE ORDER: Enviamos email con %s", template_data)
                    template_id = template_obj.sudo().create(template_data)
                    template_id.send()
                    self.need_discount_aprove = False

                    _logger.info("SALE ORDER: Enviado")
                    result={}
                    result['value'] = {'need_discount_aprove':False }
                    return result


        if gerente_encontrado == 0:
            raise ValidationError(_("No hay un gerente asignado para el almacen %s", almacen.name))
        return True

    def _get_category_needs_discount(self):
        discount_lines = self.env['res.users.discount'].search(
            [('seller_id', '=', self.env.user.id), ('almacen_id', '=', self.warehouse_id.id)], limit=1)

        descuentos_sol = []
        for order in self.order_line:

            if order.product_template_id and order.product_template_id.categ_id:

                if len(discount_lines) > 0:
                    for discount_line in discount_lines:

                        for categ in discount_line.category_ids:

                            if categ.id == order.product_template_id.categ_id.id:
                                if order.discount > discount_line.discount_permitted:
                                    descuentos_sol.append(
                                        {'producto': order.product_template_id.name, 'categoria': categ.name,
                                         'descuento_solicitado': order.discount,
                                         'descuento_permitido': discount_line.discount_permitted})

        return descuentos_sol

    def restrictions_discount(self):
        discount_lines = self.env['res.users.discount'].sudo().search(
            [('seller_id', '=', self.env.user.id), ('almacen_id', '=', self.warehouse_id.id)])

        descuentos_mayores = False
        errores_string = ''
        _logger.info("SALE ORDER::  lineas de descuento %s", discount_lines)
        for order in self.order_line:
            descuento_encontrado = 0
            if order.product_template_id and order.product_template_id.categ_id:

                for discount_line in discount_lines:

                    for categ in discount_line.category_ids:

                        if categ.id == order.product_template_id.categ_id.id:
                            descuento_encontrado = 1
                            if order.discount > discount_line.discount_permitted:
                                descuentos_mayores = True

                                errores_string += 'Advertencia!, El descuento permitido en %s para categoria %s es %s\n.' % (
                                    order.product_template_id.name, categ.name, discount_line.discount_permitted)

                if descuento_encontrado == 0 and order.discount > 0:
                    errores_string += 'Advertencia!, No tienes permitido hacer descuentos en %s' % (
                        order.product_template_id.categ_id.name)

        if descuentos_mayores == True:
            self.need_discount_aprove = True
        else:
            self.need_discount_aprove = False
        orden = self.env['sale.order'].search([('id', '=', self.id)])
        orden.write({'need_discount_aprove': descuentos_mayores})

        return {'errores': errores_string, 'need_discount_aprove': descuentos_mayores}

    def action_confirm(self):
        _logger.info("SALE ORDER::Confirmar accion")
        if self.state == 'draft':
            if self.need_discount_aprove == False:
                if self.gerente_discount_id:
                    if self.gerente_discount_id.id != self.env.user.id:
                        raise ValidationError(_("Advertencia, El gerente de descuentos debe aprobarla"))
                else:
                    dict = self.restrictions_discount()
                    if len(dict['errores']) > 0:
                        raise UserError(dict['errores'])





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


class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    user_base_discount = fields.Integer("Descuento permitido para usuarios base", default=5)
    user_gerentes_discount = fields.Integer("Descuento permitido para gerentes", default=20)
    motos_discount = fields.Integer("Descuento permitido para Motos", default=50)
