# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


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
        _log.info(" compute lots ids antes")
        res = super(StockMoveTt,self)._compute_lot_ids()
        _log.info(" compute lots ids despues")
        return res

    def _set_lot_ids(self):
        _log.info(" SETTING !! compute lots ids despues")
        super(StockMoveTt, self)._set_lot_ids()
        _log.info(" after setting !! compute lots ids despues")
        # for move in self:
        #     if move.product_id.tracking != 'serial':
        #         continue
        #     move_lines_commands = []
        #     if move.picking_type_id.show_reserved is False:
        #         mls = move.move_line_nosuggest_ids
        #     else:
        #         mls = move.move_line_ids
        #     mls = mls.filtered(lambda ml: ml.lot_id)
        #     for ml in mls:
        #         if ml.qty_done and ml.lot_id not in move.lot_ids:
        #             move_lines_commands.append((2, ml.id))
        #     ls = move.move_line_ids.lot_id
        #     for lot in move.lot_ids:
        #         if lot not in ls:
        #             move_line_vals = self._prepare_move_line_vals(quantity=0)
        #             move_line_vals['lot_id'] = lot.id
        #             move_line_vals['lot_name'] = lot.name
        #             move_line_vals['product_uom_id'] = move.product_id.uom_id.id
        #             move_line_vals['qty_done'] = 1
        #             move_lines_commands.append((0, 0, move_line_vals))
        #         else:
        #             move_line = move.move_line_ids.filtered(lambda line: line.lot_id.id == lot.id)
        #             move_line.qty_done = 1
        #     move.write({'move_line_ids': move_lines_commands})

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