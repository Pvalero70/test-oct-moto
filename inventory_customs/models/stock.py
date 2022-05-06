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


class StockMoveTt(models.Model):
    _inherit = "stock.move"

    tt_with_moto = fields.Boolean(string="Traslado de motos", compute="_compute_with_moto", store=False)

    def _compute_with_moto(self):
        for reg in self:
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
        return res


class StockMoveLineC(models.Model):
    _inherit = "stock.move.line"

    tt_motor_number = fields.Char(string="Número de motor")
    tt_color = fields.Char(string="Color")
    tt_inventory_number = fields.Char(string="Número de inventario")


class StockProductionLotTt(models.Model):
    _inherit = "stock.production.lot"

    tt_number_motor = fields.Char(string="Número de motor")
    tt_color = fields.Char(string="Color")
    tt_inventory_number = fields.Char(string="Número de inventario")