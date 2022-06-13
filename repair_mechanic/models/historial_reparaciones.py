import logging
from collections import defaultdict


from odoo import _, api, Command, fields, models
from odoo.exceptions import UserError

from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import clean_context, OrderedSet

PROCUREMENT_PRIORITIES = [('0', 'Normal'), ('1', 'Urgent')]


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

    def _action_done(self):
        """Call `_action_done` on the `stock.move` of the `stock.picking` in `self`.
        This method makes sure every `stock.move.line` is linked to a `stock.move` by either
        linking them to an existing one or a newly created one.

        If the context key `cancel_backorder` is present, backorders won't be created.

        :return: True
        :rtype: bool
        """
        _logger.info("Done Action:: 1")
        self._check_company()
        _logger.info("Done Action:: 2")
        todo_moves = self.mapped('move_lines').filtered(lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'confirmed'])
        _logger.info("Done Action:: 3")
        for picking in self:
            _logger.info("Done Action:: 4 %s",picking.name)
            if picking.owner_id:
                _logger.info("Done Action:: 5")
                picking.move_lines.write({'restrict_partner_id': picking.owner_id.id})
                _logger.info("Done Action:: 6")
                picking.move_line_ids.write({'owner_id': picking.owner_id.id})
                _logger.info("Done Action:: 7")
        _logger.info("Done Action:: 8")
        todo_moves._action_done(cancel_backorder=self.env.context.get('cancel_backorder'))
        _logger.info("Done Action:: 9")
        self.write({'date_done': fields.Datetime.now(), 'priority': '0'})
        _logger.info("Done Action:: 10")

        # if incoming moves make other confirmed/partially_available moves available, assign them
        _logger.info("Done Action:: 11")
        done_incoming_moves = self.filtered(lambda p: p.picking_type_id.code == 'incoming').move_lines.filtered(lambda m: m.state == 'done')
        _logger.info("Done Action:: 12")
        done_incoming_moves._trigger_assign()
        _logger.info("Done Action:: 13")

        self._send_confirmation_email()
        _logger.info("Done Action:: 14")
        return True

    def _action_done(self, cancel_backorder=False):
        self.filtered(lambda move: move.state == 'draft')._action_confirm()  # MRP allows scrapping draft moves
        moves = self.exists().filtered(lambda x: x.state not in ('done', 'cancel'))
        moves_ids_todo = OrderedSet()

        # Cancel moves where necessary ; we should do it before creating the extra moves because
        # this operation could trigger a merge of moves.
        for move in moves:
            if move.quantity_done <= 0 and not move.is_inventory:
                if float_compare(move.product_uom_qty, 0.0, precision_rounding=move.product_uom.rounding) == 0 or cancel_backorder:
                    move._action_cancel()

        # Create extra moves where necessary
        for move in moves:
            if move.state == 'cancel' or (move.quantity_done <= 0 and not move.is_inventory):
                continue

            moves_ids_todo |= move._create_extra_move().ids

        moves_todo = self.browse(moves_ids_todo)
        moves_todo._check_company()
        # Split moves where necessary and move quants
        backorder_moves_vals = []
        for move in moves_todo:
            # To know whether we need to create a backorder or not, round to the general product's
            # decimal precision and not the product's UOM.
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_compare(move.quantity_done, move.product_uom_qty, precision_digits=rounding) < 0:
                # Need to do some kind of conversion here
                qty_split = move.product_uom._compute_quantity(move.product_uom_qty - move.quantity_done, move.product_id.uom_id, rounding_method='HALF-UP')
                new_move_vals = move._split(qty_split)
                backorder_moves_vals += new_move_vals
        backorder_moves = self.env['stock.move'].create(backorder_moves_vals)
        # The backorder moves are not yet in their own picking. We do not want to check entire packs for those
        # ones as it could messed up the result_package_id of the moves being currently validated
        backorder_moves.with_context(bypass_entire_pack=True)._action_confirm(merge=False)
        if cancel_backorder:
            backorder_moves.with_context(moves_todo=moves_todo)._action_cancel()
        moves_todo.mapped('move_line_ids').sorted()._action_done()
        # Check the consistency of the result packages; there should be an unique location across
        # the contained quants.
        for result_package in moves_todo\
                .mapped('move_line_ids.result_package_id')\
                .filtered(lambda p: p.quant_ids and len(p.quant_ids) > 1):
            if len(result_package.quant_ids.filtered(lambda q: not float_is_zero(abs(q.quantity) + abs(q.reserved_quantity), precision_rounding=q.product_uom_id.rounding)).mapped('location_id')) > 1:
                raise UserError(_('You cannot move the same package content more than once in the same transfer or split the same package into two location.'))
        picking = moves_todo.mapped('picking_id')
        moves_todo.write({'state': 'done', 'date': fields.Datetime.now()})

        new_push_moves = moves_todo.filtered(lambda m: m.picking_id.immediate_transfer)._push_apply()
        if new_push_moves:
            new_push_moves._action_confirm()
        move_dests_per_company = defaultdict(lambda: self.env['stock.move'])
        for move_dest in moves_todo.move_dest_ids:
            move_dests_per_company[move_dest.company_id.id] |= move_dest
        for company_id, move_dests in move_dests_per_company.items():
            move_dests.sudo().with_company(company_id)._action_assign()

        # We don't want to create back order for scrap moves
        # Replace by a kwarg in master
        if self.env.context.get('is_scrap'):
            return moves_todo

        if picking and not cancel_backorder:
            backorder = picking._create_backorder()
            if any([m.state == 'assigned' for m in backorder.move_lines]):
               backorder._check_entire_pack()
        return moves_todo

class StockMoveInherit(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        _logger.info("Done stock.move:: 1")
        self.filtered(lambda move: move.state == 'draft')._action_confirm()  # MRP allows scrapping draft moves
        moves = self.exists().filtered(lambda x: x.state not in ('done', 'cancel'))
        moves_ids_todo = OrderedSet()
        _logger.info("Done stock.move:: 2")
        # Cancel moves where necessary ; we should do it before creating the extra moves because
        # this operation could trigger a merge of moves.
        for move in moves:
            if move.quantity_done <= 0 and not move.is_inventory:
                if float_compare(move.product_uom_qty, 0.0, precision_rounding=move.product_uom.rounding) == 0 or cancel_backorder:
                    move._action_cancel()
        _logger.info("Done stock.move:: 3")
        # Create extra moves where necessary
        for move in moves:
            if move.state == 'cancel' or (move.quantity_done <= 0 and not move.is_inventory):
                continue

            moves_ids_todo |= move._create_extra_move().ids
        _logger.info("Done stock.move:: 4")
        moves_todo = self.browse(moves_ids_todo)
        moves_todo._check_company()
        _logger.info("Done stock.move:: 5")
        # Split moves where necessary and move quants
        backorder_moves_vals = []
        _logger.info("Done stock.move:: 6")
        for move in moves_todo:
            # To know whether we need to create a backorder or not, round to the general product's
            # decimal precision and not the product's UOM.
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_compare(move.quantity_done, move.product_uom_qty, precision_digits=rounding) < 0:
                # Need to do some kind of conversion here
                qty_split = move.product_uom._compute_quantity(move.product_uom_qty - move.quantity_done, move.product_id.uom_id, rounding_method='HALF-UP')
                new_move_vals = move._split(qty_split)
                backorder_moves_vals += new_move_vals
        _logger.info("Done stock.move:: 7")
        backorder_moves = self.env['stock.move'].create(backorder_moves_vals)
        # The backorder moves are not yet in their own picking. We do not want to check entire packs for those
        # ones as it could messed up the result_package_id of the moves being currently validated
        backorder_moves.with_context(bypass_entire_pack=True)._action_confirm(merge=False)
        _logger.info("Done stock.move:: 8")
        if cancel_backorder:
            backorder_moves.with_context(moves_todo=moves_todo)._action_cancel()
        moves_todo.mapped('move_line_ids').sorted()._action_done()
        _logger.info("Done stock.move:: 9")
        # Check the consistency of the result packages; there should be an unique location across
        # the contained quants.
        for result_package in moves_todo\
                .mapped('move_line_ids.result_package_id')\
                .filtered(lambda p: p.quant_ids and len(p.quant_ids) > 1):
            if len(result_package.quant_ids.filtered(lambda q: not float_is_zero(abs(q.quantity) + abs(q.reserved_quantity), precision_rounding=q.product_uom_id.rounding)).mapped('location_id')) > 1:
                raise UserError(_('You cannot move the same package content more than once in the same transfer or split the same package into two location.'))
        picking = moves_todo.mapped('picking_id')
        _logger.info("Done stock.move:: 10")
        moves_todo.write({'state': 'done', 'date': fields.Datetime.now()})

        new_push_moves = moves_todo.filtered(lambda m: m.picking_id.immediate_transfer)._push_apply()
        _logger.info("Done stock.move:: 11")
        if new_push_moves:
            new_push_moves._action_confirm()
        _logger.info("Done stock.move:: 12")
        move_dests_per_company = defaultdict(lambda: self.env['stock.move'])
        _logger.info("Done stock.move:: 13")
        for move_dest in moves_todo.move_dest_ids:
            move_dests_per_company[move_dest.company_id.id] |= move_dest
        for company_id, move_dests in move_dests_per_company.items():
            move_dests.sudo().with_company(company_id)._action_assign()
        _logger.info("Done stock.move:: 14")
        # We don't want to create back order for scrap moves
        # Replace by a kwarg in master
        if self.env.context.get('is_scrap'):
            return moves_todo
        _logger.info("Done stock.move:: 15")
        if picking and not cancel_backorder:
            backorder = picking._create_backorder()
            if any([m.state == 'assigned' for m in backorder.move_lines]):
               backorder._check_entire_pack()
        _logger.info("Done stock.move:: 16")
        return moves_todo
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
