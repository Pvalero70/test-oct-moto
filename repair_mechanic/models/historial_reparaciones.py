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



class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)

        # Sanity checks.
        pickings_without_moves = self.browse()
        pickings_without_quantities = self.browse()
        pickings_without_lots = self.browse()
        products_without_lots = self.env['product.product']

        for picking in self:
            if not picking.move_lines and not picking.move_line_ids:
                pickings_without_moves |= picking

            picking.message_subscribe([self.env.user.partner_id.id])
            picking_type = picking.picking_type_id
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
            no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in picking.move_line_ids)
            if no_reserved_quantities and no_quantities_done:
                pickings_without_quantities |= picking

            if picking_type.use_create_lots or picking_type.use_existing_lots:
                lines_to_check = picking.move_line_ids
                if not no_quantities_done:
                    lines_to_check = lines_to_check.filtered(lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))
                for line in lines_to_check:
                    product = line.product_id
                    if product and product.tracking != 'none':
                        if not line.lot_name and not line.lot_id:
                            pickings_without_lots |= picking
                            products_without_lots |= product

        if not self._should_show_transfers():
            if pickings_without_moves:
                raise UserError(_('Please add some items to move.'))
            if pickings_without_quantities:
                raise UserError(self._get_without_quantities_error_message())
            if pickings_without_lots:
                raise UserError(_('You need to supply a Lot/Serial number for products %s.') % ', '.join(products_without_lots.mapped('display_name')))
        else:
            message = ""
            if pickings_without_moves:
                message += _('Transfers %s: Please add some items to move.') % ', '.join(pickings_without_moves.mapped('name'))
            if pickings_without_quantities:
                message += _('\n\nTransfers %s: You cannot validate these transfers if no quantities are reserved nor done. To force these transfers, switch in edit more and encode the done quantities.') % ', '.join(pickings_without_quantities.mapped('name'))
            if pickings_without_lots:
                message += _('\n\nTransfers %s: You need to supply a Lot/Serial number for products %s.') % (', '.join(pickings_without_lots.mapped('name')), ', '.join(products_without_lots.mapped('display_name')))
            if message:
                raise UserError(message.lstrip())
        _logger.info("Punto 1")
        # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
        # moves and/or the context and never call `_action_done`.
        _logger.info("Punto 1.1")
        if not self.env.context.get('button_validate_picking_ids'):
            _logger.info("Punto 1.2")
            self = self.with_context(button_validate_picking_ids=self.ids)
        _logger.info("Punto 1.3")
        res = self._pre_action_done_hook()
        _logger.info("Punto 1.4")
        if res is not True:
            _logger.info("Punto 1.5")
            return res
        _logger.info("Punto 5")
        # Call `_action_done`.
        if self.env.context.get('picking_ids_not_to_backorder'):
            _logger.info("Punto 5.1")
            pickings_not_to_backorder = self.browse(self.env.context['picking_ids_not_to_backorder'])
            _logger.info("Punto 5.2")
            pickings_to_backorder = self - pickings_not_to_backorder
            _logger.info("Punto 5.3")
        else:
            _logger.info("Punto 5.4")
            pickings_not_to_backorder = self.env['stock.picking']
            _logger.info("Punto 5.5")
            pickings_to_backorder = self
            _logger.info("Punto 5.6")
        _logger.info("Punto 5.7")
        pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
        _logger.info("Punto 5.8")
        pickings_to_backorder.with_context(cancel_backorder=False)._action_done()
        _logger.info("Punto 6")
        if self.user_has_groups('stock.group_reception_report') \
                and self.user_has_groups('stock.group_auto_reception_report') \
                and self.filtered(lambda p: p.picking_type_id.code != 'outgoing'):
            lines = self.move_lines.filtered(lambda m: m.product_id.type == 'product' and m.state != 'cancel' and m.quantity_done and not m.move_dest_ids)
            if lines:
                # don't show reception report if all already assigned/nothing to assign
                wh_location_ids = self.env['stock.location']._search([('id', 'child_of', self.picking_type_id.warehouse_id.view_location_id.id), ('usage', '!=', 'supplier')])
                if self.env['stock.move'].search([
                        ('state', 'in', ['confirmed', 'partially_available', 'waiting', 'assigned']),
                        ('product_qty', '>', 0),
                        ('location_id', 'in', wh_location_ids),
                        ('move_orig_ids', '=', False),
                        ('picking_id', 'not in', self.ids),
                        ('product_id', 'in', lines.product_id.ids)], limit=1):
                    action = self.action_view_reception_report()
                    action['context'] = {'default_picking_ids': self.ids}
                    return action
        return True


'''
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

'''
