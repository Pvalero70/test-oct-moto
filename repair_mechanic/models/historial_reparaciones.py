import logging


from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.tools.float_utils import float_compare, float_is_zero

_logger = logging.getLogger(__name__)



class ProductProductRepair(models.Model):
    _inherit = 'product.product'
    _order = 'orden_repairs desc'

    orden_repairs = fields.Integer('Orden en Reparaciones',default=0)


class RepairMechanic(models.Model):
    _inherit = 'repair.order'

    @api.onchange('partner_id')
    def _products_order(self):
        _logger.info("En onchange partner")
        products = self.env['product.product'].search([('type', 'in', ['product', 'consu']),('company_id', 'in', [self.env.company.id,'',None,False])])
        ordenes_ventas = self.env['pos.order'].search([('partner_id','=',self.partner_id.id),('state','in',['done','invoiced','paid'])])
        productos_ventas = [product for orden in ordenes_ventas for line in orden.lines for product in line.product_id ]
        _logger.info("Domain %s",products)
        _logger.info("Ventas %s",productos_ventas)
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
        _logger.info("Productos Encontrados motos %s",[p for p in products if p.orden_repairs == 1])

    def action_incoming(self):
        _logger.info("En mi boton")

        res = super(RepairMechanic, self).action_incoming()

        if self.product_id and self.lot_id:
            if self.product_id.orden_repairs == 1 and self.lot_id.product_qty == 1:
                _logger.info("En mi Descontamos 1")
                self.lot_id.product_qty = 0
                self.lot_id.write({'product_qty':0})
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
                    if categoria.name == 'Motos':
                        return
                    while categoria.parent_id:
                        categoria = categoria.parent_id
                        if categoria.name == 'Motos':
                            return 
                raise ValidationError(
                    _('The serial number has already been assigned: \n Product: %s, Serial Number: %s') % (
                    quant.product_id.display_name, quant.lot_id.name))


