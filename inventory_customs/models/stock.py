# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.tools.misc import clean_context, OrderedSet
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
import logging
from odoo.osv import expression
from odoo.exceptions import ValidationError, UserError
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

    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
        """ Create or update move lines.
        """
        self.ensure_one()

        if not lot_id:
            lot_id = self.env['stock.production.lot']
        if not package_id:
            package_id = self.env['stock.quant.package']
        if not owner_id:
            owner_id = self.env['res.partner']

        # do full packaging reservation when it's needed
        if self.product_packaging_id and self.product_id.product_tmpl_id.categ_id.packaging_reserve_method == "full":
            available_quantity = self.product_packaging_id._check_qty(available_quantity, self.product_id.uom_id, "DOWN")

        taken_quantity = min(available_quantity, need)

        # `taken_quantity` is in the quants unit of measure. There's a possibility that the move's
        # unit of measure won't be respected if we blindly reserve this quantity, a common usecase
        # is if the move's unit of measure's rounding does not allow fractional reservation. We chose
        # to convert `taken_quantity` to the move's unit of measure with a down rounding method and
        # then get it back in the quants unit of measure with an half-up rounding_method. This
        # way, we'll never reserve more than allowed. We do not apply this logic if
        # `available_quantity` is brought by a chained move line. In this case, `_prepare_move_line_vals`
        # will take care of changing the UOM to the UOM of the product.
        if not strict and self.product_id.uom_id != self.product_uom:
            taken_quantity_move_uom = self.product_id.uom_id._compute_quantity(taken_quantity, self.product_uom, rounding_method='DOWN')
            taken_quantity = self.product_uom._compute_quantity(taken_quantity_move_uom, self.product_id.uom_id, rounding_method='HALF-UP')

        quants = []
        rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        if self.product_id.tracking == 'serial':
            if float_compare(taken_quantity, int(taken_quantity), precision_digits=rounding) != 0:
                taken_quantity = 0

        try:
            with self.env.cr.savepoint():
                if not float_is_zero(taken_quantity, precision_rounding=self.product_id.uom_id.rounding):
                    if  self.picking_id.ic_sale_order:
                        quants = self.env['stock.quant']._update_reserved_quantity(
                            self.product_id, location_id, taken_quantity, lot_id=lot_id,
                            package_id=package_id, owner_id=owner_id, strict=strict, ic_order=self.picking_id.ic_sale_order
                        )
                    else:
                        quants = self.env['stock.quant']._update_reserved_quantity(
                            self.product_id, location_id, taken_quantity, lot_id=lot_id,
                            package_id=package_id, owner_id=owner_id, strict=strict
                        )
                    _log.info(" QUANTS desde stock move ::: %s " % quants)
        except UserError:
            taken_quantity = 0

        # Find a candidate move line to update or create a new one.
        for reserved_quant, quantity in quants:
            to_update = next((line for line in self.move_line_ids if line._reservation_is_updatable(quantity, reserved_quant)), False)
            if to_update:
                uom_quantity = self.product_id.uom_id._compute_quantity(quantity, to_update.product_uom_id, rounding_method='HALF-UP')
                uom_quantity = float_round(uom_quantity, precision_digits=rounding)
                uom_quantity_back_to_product_uom = to_update.product_uom_id._compute_quantity(uom_quantity, self.product_id.uom_id, rounding_method='HALF-UP')
            if to_update and float_compare(quantity, uom_quantity_back_to_product_uom, precision_digits=rounding) == 0:
                to_update.with_context(bypass_reservation_update=True).product_uom_qty += uom_quantity
            else:
                if self.product_id.tracking == 'serial':
                    # Crea las lineas con el LOT ID asignado ----->>>>
                    self.env['stock.move.line'].create([self._prepare_move_line_vals(quantity=1, reserved_quant=reserved_quant) for i in range(int(quantity))])
                else:
                    self.env['stock.move.line'].create(self._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant))
        return taken_quantity

    
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


class StockProductionLotTt(models.Model):
    _inherit = "stock.production.lot"

    tt_number_motor = fields.Char(string="Número de motor")
    tt_color = fields.Char(string="Color")
    tt_inventory_number = fields.Char(string="Número de inventario")

    tt_free_optional = fields.Char(string="Opcionales libres")
    tt_company_currency_id = fields.Many2one('res.currency', default=lambda self: self._default_currency_id())
    tt_adc_costs = fields.Monetary(currency_field="tt_company_currency_id", string="Costos adicionales")

    can_edit_free_optional = fields.Boolean(string="Puede editar opcionales libres. ", compute="_check_if_can_edit")
    can_edit_adc_costs = fields.Boolean(string="Puede editar opcionales libres. ", compute="_check_if_can_edit")

    def _check_if_can_edit(self):
        self.can_edit_free_optional = True if self.env.user.has_group('inventory_customs.group_edit_free_optionals') else False
        self.can_edit_adc_costs = True if self.env.user.has_group('inventory_customs.group_edit_additional_costs') else False

    def _default_currency_id(self):
        return self.env.user.company_id.currency_id

    def _hide_snf(self):
        self.hide_snf_fields = self.env.company.restrict_inv_sn_flow
    hide_snf_fields = fields.Boolean('Ocultar campos tt', compute="_hide_snf", store=False)

    @api.constrains('tt_number_motor', 'tt_inventory_number')
    def _check_motor_inventory_unique_numbers(self):
        if self.env.company.restrict_inv_sn_flow:
            return False
        for reg in self:
            if reg.tt_number_motor:
                other_reg_motor = self.env['stock.production.lot'].search([('tt_number_motor', '=', reg.tt_number_motor), ('id', '!=', reg.id)])
                if other_reg_motor:
                    raise UserError("El número de motor debe ser único")
            if reg.tt_inventory_number:
                other_reg_inventory = self.env['stock.production.lot'].search([('tt_inventory_number', '=', reg.tt_inventory_number), ('id', '!=', reg.id)])
                if other_reg_inventory:
                    raise UserError("El número de inventario debe ser único")


class StockQuantTti(models.Model):
    _inherit = "stock.quant"

    inv_number = fields.Char(string="Número de inventario.", related="lot_id.tt_inventory_number")
    free_adds = fields.Char(string="Adicionales", related="lot_id.tt_free_optional")
    tt_number_motor = fields.Char(string="Número de motor.", related="lot_id.tt_number_motor")
    tt_color = fields.Char(string="Color", related="lot_id.tt_color")

    # def _hide_snf(self):
    #     self.hide_snf_fields = self.env.company.restrict_inv_sn_flow
    #
    # hide_snf_fields = fields.Boolean('Ocultar campos tt', compute="_hide_snf", store=False)

    def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, strict=False, ic_order=None):
        """ Increase the reserved quantity, i.e. increase `reserved_quantity` for the set of quants
        sharing the combination of `product_id, location_id` if `strict` is set to False or sharing
        the *exact same characteristics* otherwise. Typically, this method is called when reserving
        a move or updating a reserved move line. When reserving a chained move, the strict flag
        should be enabled (to reserve exactly what was brought). When the move is MTS,it could take
        anything from the stock, so we disable the flag. When editing a move line, we naturally
        enable the flag, to reflect the reservation according to the edition.

        :return: a list of tuples (quant, quantity_reserved) showing on which quant the reservation
            was done and how much the system was able to reserve on it
        """
        self = self.sudo()
        rounding = product_id.uom_id.rounding
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)
        _log.info(" UPDATE RESERVED QUANTS ::: %s " % quants)
        reserved_quants = []



        if float_compare(quantity, 0, precision_rounding=rounding) > 0:
            # if we want to reserve
            available_quantity = sum(quants.filtered(lambda q: float_compare(q.quantity, 0, precision_rounding=rounding) > 0).mapped('quantity')) - sum(quants.mapped('reserved_quantity'))
            _log.info(" AV QUANTITY ::: %s " % available_quantity)
            if float_compare(quantity, available_quantity, precision_rounding=rounding) > 0:
                raise UserError(_('It is not possible to reserve more products of %s than you have in stock.', product_id.display_name))
        elif float_compare(quantity, 0, precision_rounding=rounding) < 0:
            # if we want to unreserve
            available_quantity = sum(quants.mapped('reserved_quantity'))
            if float_compare(abs(quantity), available_quantity, precision_rounding=rounding) > 0:
                raise UserError(_('It is not possible to unreserve more products of %s than you have in stock.', product_id.display_name))
        else:
            return reserved_quants

      
        if ic_order is not None:
            lots = ic_order.order_line.filtered(lambda l: l.lot_id != False).mapped('lot_id')
            if lots:
                quants = quants.filtered(lambda q: q.lot_id.id in lots.ids)
        
        for quant in quants:
            if float_compare(quantity, 0, precision_rounding=rounding) > 0:
                max_quantity_on_quant = quant.quantity - quant.reserved_quantity 
                if float_compare(max_quantity_on_quant, 0, precision_rounding=rounding) <= 0:
                    continue
                max_quantity_on_quant = min(max_quantity_on_quant, quantity)
                quant.reserved_quantity += max_quantity_on_quant 
                reserved_quants.append((quant, max_quantity_on_quant)) 
                quantity -= max_quantity_on_quant                      
                available_quantity -= max_quantity_on_quant             
            else:
                max_quantity_on_quant = min(quant.reserved_quantity, abs(quantity))
                quant.reserved_quantity -= max_quantity_on_quant
                reserved_quants.append((quant, -max_quantity_on_quant))
                quantity += max_quantity_on_quant
                available_quantity += max_quantity_on_quant

            if float_is_zero(quantity, precision_rounding=rounding) or float_is_zero(available_quantity, precision_rounding=rounding):
                break
        return reserved_quants

    