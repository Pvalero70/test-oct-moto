import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning

_logger = logging.getLogger(__name__)


class ProductProductRepair(models.Model):
    _inherit = 'product.product'

    orden_repairs = fields.Integer('Orden en Reparaciones',default=0)


class RepairMechanic(models.Model):
    _inherit = 'repair.order'

    @api.onchange('partner_id')
    def _products_order(self):
        _logger.info("En onchange partner")
        products = self.env['product.product'].search([('type', 'in', ['product', 'consu']),'|', ('company_id', '=', self.env.company.id),('company_id','=',None)], limit=3)
        ordenes_ventas = self.env['pos.order'].search([('partner_id','=',self.partner_id.id),('state','in',['done','invoiced'])])
        productos_ventas = [product for orden in ordenes_ventas for line in orden.line for product in line.product_id ]
        _logger.info("Domain %s",products)
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
