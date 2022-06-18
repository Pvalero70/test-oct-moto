import logging
from collections import defaultdict


from odoo import _, api, Command, fields, models
from odoo.exceptions import UserError

from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import clean_context, OrderedSet
from odoo.exceptions import ValidationError

PROCUREMENT_PRIORITIES = [('0', 'Normal'), ('1', 'Urgent')]


_logger = logging.getLogger(__name__)

class StockProductionLotRepair(models.Model):
    _inherit = 'stock.production.lot'

    is_repair_moto_action = fields.Boolean("Esta operacion proviene de una reparacion de una moto ?",default=False)

class ProductProductRepair(models.Model):
    _inherit = 'product.product'

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        ctx = self._context
        if 'order_display' in ctx:
            order = ctx['order_display']
            return self._search(args, limit=limit, access_rights_uid=name_get_uid, order=order)
        _logger.info("Name search")
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)



    orden_repairs = fields.Integer('Orden que se mostarara el Many2one en Reparaciones',default=0)


class RepairMechanic(models.Model):
    _inherit = 'repair.order'

    @api.onchange('partner_id')
    def _products_order(self):
        _logger.info("En onchange partner")
        products = self.env['product.product'].search([('type', 'in', ['product', 'consu']),('company_id', 'in', [self.env.company.id,'',None,False])])
        ordenes_ventas = self.env['pos.order'].search([('partner_id','=',self.partner_id.id),('state','in',['done','invoiced','paid'])])
        productos_ventas = [product for orden in ordenes_ventas for line in orden.lines for product in line.product_id ]

        for product in products:
            product_encontrado = False
            for product_venta in productos_ventas:
                if product.id == product_venta.id:
                    if product.categ_id:
                        categoria = product.categ_id
                        if categoria.name =='Motos':
                            product.orden_repairs = 1
                            product_encontrado = True
                            break
                        while categoria.parent_id:
                            categoria = categoria.parent_id
                            if categoria.name == 'Motos':
                                product.orden_repairs = 1
                                product_encontrado = True
                                break
                        if product_encontrado:
                            break
            if not product_encontrado:
                product.orden_repairs = 0


    def action_incoming(self):
        res = super(RepairMechanic, self).action_incoming()
        for pick in self.picking_ids:
            pick.lot_id_product = self.lot_id
        return res



class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    lot_id_product = fields.Many2one('stock.production.lot')

    def button_validate(self):
        if self.lot_id_product:
            #Si existe este campo es que proviene de una reparacion
            self.lot_id_product.is_repair_moto_action = True

        res = super(StockPickingInherit, self).button_validate()

        # Ponemos en False para que el codigo ya no afecte a otras recepciones de motos y sigan las validaciones normales de odoo
        self.lot_id_product.is_repair_moto_action = False

        return res


class StockQuantInherit(models.Model):
    _inherit = 'stock.quant'

    @api.constrains('quantity')
    def check_quantity(self):
        for quant in self:
            if quant.location_id.usage != 'inventory' and quant.lot_id and quant.product_id.tracking == 'serial' \
                    and float_compare(abs(quant.quantity), 1, precision_rounding=quant.product_uom_id.rounding) > 0:
                if quant.lot_id.product_id:
                    product = quant.lot_id.product_id
                    categoria = product.categ_id
                    if quant.lot_id.is_repair_moto_action:
                        if categoria.name == 'Motos':
                            return
                        while categoria.parent_id:
                            categoria = categoria.parent_id
                            if categoria.name == 'Motos':
                                return
                raise ValidationError(
                    _('The serial number has already been assigned: \n Product: %s, Serial Number: %s') % (
                    quant.product_id.display_name, quant.lot_id.name))


