# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.tools.misc import clean_context, OrderedSet
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
import logging
from odoo.exceptions import ValidationError
import re
_log = logging.getLogger("___name: %s" % __name__)
CUSTOM_NUMBERS_PATTERN = re.compile(r'[0-9]{2}  [0-9]{2}  [0-9]{4}  [0-9]{7}')


class StockPickingTt(models.Model):
    _inherit = "stock.picking"

    ic_sale_order = fields.Many2one('sale.order', string="InventoryCustom Order")

    tt_aduana = fields.Char(string="Aduana")
    tt_aduana_date_in = fields.Date(string="Fecha ingreso")
    tt_num_pedimento = fields.Char(
        help="Campo opcional para ingresar la información aduanera en el caso de ventas de bienes importados de primera mano o en el caso de operaciones de comercio exterior con bienes o servicios.\n"
            "El formato debe ser:\n"
            " - 2 dígitos del año de validación seguido por dos espacios.\n"
            " - 2 dígitos del despacho de aduana seguido de dos espacios.\n"
            " - 4 dígitos del numero de serial seguido por dos espacios.\n"
            " - 1 dígito correspondiente al ultimo dígito del año actual, excepto en el caso de una aduana consolidada iniciada en el año anterior a la solicitud original de rectificación.\n"
            " - 6 dígitos de la numeración progresiva de la aduana.",
        string='Número de pedimento',
        copy=False)

    # -------------------------------------------------------------------------
    # CONSTRAINT METHODS
    # -------------------------------------------------------------------------

    @api.constrains('tt_num_pedimento')
    def _check_l10n_mx_edi_customs_number(self):
        if self.env.company.restrict_inv_sn_flow:
            return False
        for reg in self:
            if not reg.tt_num_pedimento:
                continue
            if not CUSTOM_NUMBERS_PATTERN.match(reg.tt_num_pedimento):
                raise ValidationError(_("El número de pedimento es invalido, debe tener un patrón semejante a: 15  48  3009  0001234 "))

    def _hide_snf(self):
        self.hide_snf_fields = self.env.company.restrict_inv_sn_flow

    hide_snf_fields = fields.Boolean('Ocultar campos tt', compute="_hide_snf", store=False)

    # -------------------------------------------------------------------------
    # INHERED METHODS
    # -------------------------------------------------------------------------

    @api.model
    def create(self, vals):
        picking = super(StockPickingTt, self).create(vals)
        # Create move lines
        # mlids = []
        if 'ic_sale_id' in self._context:
            sale_id = self.env['sale.order'].browse(self._context.get('ic_sale_id'))
            if not sale_id:
                return picking
            # Revisa si tiene al menos 1 producto con el número de serie especifico.
            lines_w_serial = sale_id.order_line.filtered(lambda l: l.lot_id is not False)
            if sale_id and lines_w_serial:
                picking.ic_sale_order = sale_id.id
        return picking


class StockMoveTt(models.Model):
    _inherit = "stock.move"

    tt_with_moto = fields.Boolean(string="Traslado de motos", compute="_compute_with_moto", store=False)

    def _compute_with_moto(self):
        for reg in self:
            if self.env.company.restrict_inv_sn_flow:
                reg.tt_with_moto = False
                continue
            if reg.product_id.product_inv_categ and reg.product_id.product_inv_categ in ["moto", "Moto"]:
                reg.tt_with_moto = True
            else:
                reg.tt_with_moto = False

    @api.depends('move_line_ids', 'move_line_ids.lot_id', 'move_line_ids.qty_done')
    def _compute_lot_ids(self):
        res = super(StockMoveTt,self)._compute_lot_ids()
        if self.env.company.restrict_inv_sn_flow:
            return res
        for move in self:
            if move.move_line_nosuggest_ids:
                for ml in move.move_line_nosuggest_ids:
                    if ml.lot_id and ml.tt_motor_number and ml.tt_color and ml.tt_inventory_number:
                        ml.lot_id.tt_number_motor = ml.tt_motor_number
                        ml.lot_id.tt_color = ml.tt_color
                        ml.lot_id.tt_inventory_number = ml.tt_inventory_number
                        ml.lot_id.tt_free_optional = ml.tt_free_optional
                        ml.lot_id.tt_adc_costs = ml.tt_adc_costs
        return res

    @api.onchange("move_line_nosuggest_ids")
    def calc_inv_number(self):
        _log.info("\n\n ===>> padre original :: %s PADRE: %s Hijos: %s " % (self._origin, self, self.move_line_nosuggest_ids))
        # Buscamos el último puesto en el wizard (no guardado)
        mlns_with_inv_num = self.move_line_nosuggest_ids.filtered(lambda x: x.tt_inventory_number_seq is not False)
        mlns_to_calc = self.move_line_nosuggest_ids.filtered(lambda x: not x.tt_inventory_number_seq)
        invn_num_self_max = 0
        # We search in the same document
        if mlns_with_inv_num:
            for mlns in mlns_with_inv_num:
                invn_num_self_max = mlns.tt_inventory_number_seq if mlns.tt_inventory_number_seq > invn_num_self_max else invn_num_self_max
        # Buscamos el último guardado.
        last_ml = self.env['stock.move.line'].search(
            [('tt_inventory_number_seq', '!=', False), ('company_id', '=', self.company_id.id)],
            order="tt_inventory_number_seq desc", limit=1)
        # we search other documents inside.
        if last_ml:
            _log.info("\n\n El mayor de otros documentos :: %s " % last_ml.tt_inventory_number_seq)
            if invn_num_self_max > last_ml.tt_inventory_number_seq:
                # The max seq is in self.
                next_seq = invn_num_self_max + 1
            else:
                # Max is in other documents.
                next_seq = last_ml.tt_inventory_number_seq + 1
        else:
            # Max is in self
            next_seq = invn_num_self_max + 1

        # Establecemos el mayor de los dos anteriores + 1 como el que debe establecerse, lo establecemos.
        for mln in mlns_to_calc:
            mln.tt_inventory_number_seq = next_seq
            mln.tt_inventory_number = str(next_seq).zfill(4)
            next_seq += 1

    # -------------------------------------------------------------------------
    # CONSTRAINT METHODS
    # -------------------------------------------------------------------------

    @api.constrains('move_line_nosuggest_ids')
    def _check_inventory_number_uniq(self):
        if self.env.company.restrict_inv_sn_flow:
            return False
        for reg in self:
            for line in reg.move_line_nosuggest_ids:
                if line.tt_inventory_number:
                    other_lines = self.env['stock.move.line'].search([
                        ('tt_inventory_number', '=', line.tt_inventory_number),
                        ('company_id', '=', line.company_id.id),
                        ('id', '!=', line.id)
                    ])
                    if other_lines:
                        raise ValidationError("No puede duplicarse el número de inventario para la misma compañia (%s)" % line.tt_inventory_number)
                if line.tt_motor_number:
                    other_lines_motor = self.env['stock.move.line'].search([
                        ('tt_motor_number', '=', line.tt_motor_number),
                        ('company_id', '=', line.company_id.id),
                        ('id', '!=', line.id)
                    ])
                    if other_lines_motor:
                        raise ValidationError(
                            "No puede duplicarse el número de motor para la misma compañia (%s)" % line.tt_motor_number)

    # -------------------------------------------------------------------------
    # FORCE LOT METHODS
    # -------------------------------------------------------------------------

    def _action_assign(self):
        """ Reserve stock moves by creating their stock move lines. A stock move is
        considered reserved once the sum of `product_qty` for all its move lines is
        equal to its `product_qty`. If it is less, the stock move is considered
        partially available.
        """

        def _get_available_move_lines(move):
            move_lines_in = move.move_orig_ids.filtered(lambda m: m.state == 'done').mapped('move_line_ids')
            keys_in_groupby = ['location_dest_id', 'lot_id', 'result_package_id', 'owner_id']

            def _keys_in_sorted(ml):
                return (ml.location_dest_id.id, ml.lot_id.id, ml.result_package_id.id, ml.owner_id.id)

            grouped_move_lines_in = {}
            for k, g in groupby(sorted(move_lines_in, key=_keys_in_sorted), key=itemgetter(*keys_in_groupby)):
                qty_done = 0
                for ml in g:
                    qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                grouped_move_lines_in[k] = qty_done
            move_lines_out_done = (move.move_orig_ids.mapped('move_dest_ids') - move)\
                .filtered(lambda m: m.state in ['done'])\
                .mapped('move_line_ids')
            # As we defer the write on the stock.move's state at the end of the loop, there
            # could be moves to consider in what our siblings already took.
            moves_out_siblings = move.move_orig_ids.mapped('move_dest_ids') - move
            moves_out_siblings_to_consider = moves_out_siblings & (StockMove.browse(assigned_moves_ids) + StockMove.browse(partially_available_moves_ids))
            reserved_moves_out_siblings = moves_out_siblings.filtered(lambda m: m.state in ['partially_available', 'assigned'])
            move_lines_out_reserved = (reserved_moves_out_siblings | moves_out_siblings_to_consider).mapped('move_line_ids')
            keys_out_groupby = ['location_id', 'lot_id', 'package_id', 'owner_id']

            def _keys_out_sorted(ml):
                return (ml.location_id.id, ml.lot_id.id, ml.package_id.id, ml.owner_id.id)

            grouped_move_lines_out = {}
            for k, g in groupby(sorted(move_lines_out_done, key=_keys_out_sorted), key=itemgetter(*keys_out_groupby)):
                qty_done = 0
                for ml in g:
                    qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                grouped_move_lines_out[k] = qty_done
            for k, g in groupby(sorted(move_lines_out_reserved, key=_keys_out_sorted), key=itemgetter(*keys_out_groupby)):
                grouped_move_lines_out[k] = sum(self.env['stock.move.line'].concat(*list(g)).mapped('product_qty'))
            available_move_lines = {key: grouped_move_lines_in[key] - grouped_move_lines_out.get(key, 0) for key in grouped_move_lines_in}
            # pop key if the quantity available amount to 0
            rounding = move.product_id.uom_id.rounding
            return dict((k, v) for k, v in available_move_lines.items() if float_compare(v, 0, precision_rounding=rounding) > 0)

        StockMove = self.env['stock.move']
        assigned_moves_ids = OrderedSet()
        partially_available_moves_ids = OrderedSet()
        # Read the `reserved_availability` field of the moves out of the loop to prevent unwanted
        # cache invalidation when actually reserving the move.
        reserved_availability = {move: move.reserved_availability for move in self}
        roundings = {move: move.product_id.uom_id.rounding for move in self}
        move_line_vals_list = []
        # Once the quantities are assigned, we want to find a better destination location thanks
        # to the putaway rules. This redirection will be applied on moves of `moves_to_redirect`.
        moves_to_redirect = OrderedSet()
        for move in self.filtered(lambda m: m.state in ['confirmed', 'waiting', 'partially_available']):
            rounding = roundings[move]
            missing_reserved_uom_quantity = move.product_uom_qty - reserved_availability[move]
            missing_reserved_quantity = move.product_uom._compute_quantity(missing_reserved_uom_quantity, move.product_id.uom_id, rounding_method='HALF-UP')
            if move._should_bypass_reservation():
                # create the move line(s) but do not impact quants
                if move.move_orig_ids:
                    available_move_lines = _get_available_move_lines(move)
                    for (location_id, lot_id, package_id, owner_id), quantity in available_move_lines.items():
                        qty_added = min(missing_reserved_quantity, quantity)
                        move_line_vals = move._prepare_move_line_vals(qty_added)
                        _log.info(" LOT ID ::: %s " % lot_id)
                        move_line_vals.update({
                            'location_id': location_id.id,
                            'lot_id': lot_id.id,
                            'lot_name': lot_id.name,
                            'owner_id': owner_id.id,
                        })
                        move_line_vals_list.append(move_line_vals)
                        missing_reserved_quantity -= qty_added
                        if float_is_zero(missing_reserved_quantity, precision_rounding=move.product_id.uom_id.rounding):
                            break

                if missing_reserved_quantity and move.product_id.tracking == 'serial' and (move.picking_type_id.use_create_lots or move.picking_type_id.use_existing_lots):
                    for i in range(0, int(missing_reserved_quantity)):
                        move_line_vals_list.append(move._prepare_move_line_vals(quantity=1))
                elif missing_reserved_quantity:
                    to_update = move.move_line_ids.filtered(lambda ml: ml.product_uom_id == move.product_uom and
                                                            ml.location_id == move.location_id and
                                                            ml.location_dest_id == move.location_dest_id and
                                                            ml.picking_id == move.picking_id and
                                                            not ml.lot_id and
                                                            not ml.package_id and
                                                            not ml.owner_id)
                    if to_update:
                        to_update[0].product_uom_qty += move.product_id.uom_id._compute_quantity(
                            missing_reserved_quantity, move.product_uom, rounding_method='HALF-UP')
                    else:
                        move_line_vals_list.append(move._prepare_move_line_vals(quantity=missing_reserved_quantity))
                assigned_moves_ids.add(move.id)
                moves_to_redirect.add(move.id)
            else:
                if float_is_zero(move.product_uom_qty, precision_rounding=move.product_uom.rounding):
                    assigned_moves_ids.add(move.id)
                elif not move.move_orig_ids:
                    if move.procure_method == 'make_to_order':
                        continue
                    # If we don't need any quantity, consider the move assigned.
                    need = missing_reserved_quantity
                    if float_is_zero(need, precision_rounding=rounding):
                        assigned_moves_ids.add(move.id)
                        continue
                    # Reserve new quants and create move lines accordingly.
                    forced_package_id = move.package_level_id.package_id or None
                    available_quantity = move._get_available_quantity(move.location_id, package_id=forced_package_id)
                    if available_quantity <= 0:
                        continue
                    taken_quantity = move._update_reserved_quantity(need, available_quantity, move.location_id, package_id=forced_package_id, strict=False)
                    if float_is_zero(taken_quantity, precision_rounding=rounding):
                        continue
                    moves_to_redirect.add(move.id)
                    if float_compare(need, taken_quantity, precision_rounding=rounding) == 0:
                        assigned_moves_ids.add(move.id)
                    else:
                        partially_available_moves_ids.add(move.id)
                else:
                    # Check what our parents brought and what our siblings took in order to
                    # determine what we can distribute.
                    # `qty_done` is in `ml.product_uom_id` and, as we will later increase
                    # the reserved quantity on the quants, convert it here in
                    # `product_id.uom_id` (the UOM of the quants is the UOM of the product).
                    available_move_lines = _get_available_move_lines(move)
                    if not available_move_lines:
                        continue
                    for move_line in move.move_line_ids.filtered(lambda m: m.product_qty):
                        if available_move_lines.get((move_line.location_id, move_line.lot_id, move_line.result_package_id, move_line.owner_id)):
                            available_move_lines[(move_line.location_id, move_line.lot_id, move_line.result_package_id, move_line.owner_id)] -= move_line.product_qty
                    for (location_id, lot_id, package_id, owner_id), quantity in available_move_lines.items():
                        need = move.product_qty - sum(move.move_line_ids.mapped('product_qty'))
                        # `quantity` is what is brought by chained done move lines. We double check
                        # here this quantity is available on the quants themselves. If not, this
                        # could be the result of an inventory adjustment that removed totally of
                        # partially `quantity`. When this happens, we chose to reserve the maximum
                        # still available. This situation could not happen on MTS move, because in
                        # this case `quantity` is directly the quantity on the quants themselves.
                        available_quantity = move._get_available_quantity(location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
                        if float_is_zero(available_quantity, precision_rounding=rounding):
                            continue
                        taken_quantity = move._update_reserved_quantity(need, min(quantity, available_quantity), location_id, lot_id, package_id, owner_id)
                        if float_is_zero(taken_quantity, precision_rounding=rounding):
                            continue
                        moves_to_redirect.add(move.id)
                        if float_is_zero(need - taken_quantity, precision_rounding=rounding):
                            assigned_moves_ids.add(move.id)
                            break
                        partially_available_moves_ids.add(move.id)
            if move.product_id.tracking == 'serial':
                move.next_serial_count = move.product_uom_qty
        _log.info(" MOVE LINE LIST:: %s " % move_line_vals_list)
        self.env['stock.move.line'].create(move_line_vals_list)
        StockMove.browse(partially_available_moves_ids).write({'state': 'partially_available'})
        StockMove.browse(assigned_moves_ids).write({'state': 'assigned'})
        if self.env.context.get('bypass_entire_pack'):
            return
        self.mapped('picking_id')._check_entire_pack()
        StockMove.browse(moves_to_redirect).move_line_ids._apply_putaway_strategy()


class StockMoveLineC(models.Model):
    _inherit = "stock.move.line"

    tt_motor_number = fields.Char(string="Número de motor")
    tt_color = fields.Char(string="Color")
    tt_inventory_number = fields.Char(string="Número de inventario")
    tt_inventory_number_seq = fields.Integer(string="Secuencia")
    tt_free_optional = fields.Char(string="Opcionales libres")
    tt_company_currency_id = fields.Many2one('res.currency', default=lambda self: self._default_currency_id())
    tt_adc_costs = fields.Monetary(currency_field="tt_company_currency_id", string="Costos adicionales")

    def _default_currency_id(self):
        return self.env.user.company_id.currency_id

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            if vals['lot_id']:
                _log.info("CREATE SML ::: %s " % vals_list)
                x = 1/0
        res = super(StockMoveLineC, self).create(vals_list)
        return res

    # def write(self, vals):
    #     _log.info(" WRITE VALS :: %s " % vals)
    #     return super(StockMoveLineC, self).write(vals)

class StockProductionLotTt(models.Model):
    _inherit = "stock.production.lot"

    tt_number_motor = fields.Char(string="Número de motor")
    tt_color = fields.Char(string="Color")
    tt_inventory_number = fields.Char(string="Número de inventario")

    tt_free_optional = fields.Char(string="Opcionales libres")
    tt_company_currency_id = fields.Many2one('res.currency', default=lambda self: self._default_currency_id())
    tt_adc_costs = fields.Monetary(currency_field="tt_company_currency_id", string="Costos adicionales")

    def _default_currency_id(self):
        return self.env.user.company_id.currency_id

    def _hide_snf(self):
        self.hide_snf_fields = self.env.company.restrict_inv_sn_flow
    hide_snf_fields = fields.Boolean('Ocultar campos tt', compute="_hide_snf", store=False)


class StockQuantTti(models.Model):
    _inherit = "stock.quant"

    inv_number = fields.Char(string="Número de inventario.", related="lot_id.tt_inventory_number")

    # def _hide_snf(self):
    #     self.hide_snf_fields = self.env.company.restrict_inv_sn_flow
    #
    # hide_snf_fields = fields.Boolean('Ocultar campos tt', compute="_hide_snf", store=False)


