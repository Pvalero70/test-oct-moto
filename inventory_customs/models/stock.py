# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
import logging
from odoo.exceptions import ValidationError
import re
_log = logging.getLogger("___name: %s" % __name__)
CUSTOM_NUMBERS_PATTERN = re.compile(r'[0-9]{2}  [0-9]{2}  [0-9]{4}  [0-9]{7}')


class StockPickingTt(models.Model):
    _inherit = "stock.picking"

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
