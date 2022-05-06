# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
_log = logging.getLogger("___name: %s" % __name__)


class AccountMoveItt(models.Model):
    _inherit = "account.move"

    def _print_moto_details(self):
        """
        Check if this invoice is for moto product, and some rules (like only one product)
        only one product for this kind of product.
        :return: True if is an invoice for moto, False else.
        """
        # Only one line.
        # if self.invoice_line_ids and len(self.invoice_line_ids.ids) > 1:
        #     return False
        moto_lines = self.invoice_line_ids.filtered(lambda p: p.product_id.product_inv_categ in ["moto", "Moto"])
        if moto_lines and len(moto_lines.ids) == len(self.invoice_line_ids.ids):
            return True
        return False

    def _get_invoiced_lot_values_tt(self):
        # Poner aquí la restricción de la compañia.
        if self.move_type != "out_invoice" or self.state == 'draft':
            return False
        data = []
        if not self.pos_order_ids:
            return False
        pols = self.pos_order_ids.mapped('lines').mapped('pack_lot_ids')
        _log.info("\n POS ORDER LINE FOUND:: %s" % pols)
        # Get all stock production lot  records in the same query.
        lot_domains = [
            ('name', 'in', pols.mapped('lot_name')),
            ('product_id', 'in', pols.mapped('product_id').ids),
        ]
        ori_lots = self.env['stock.production.lot'].search(lot_domains)
        _log.info("\nORI LOTS FOUND:::  %s " % ori_lots)
        if not ori_lots:
            return False
        sml_ids = self.env['stock.move.line'].search([
            ('lot_id', 'in', ori_lots.ids),
            ('tt_motor_number', '!=', False),
            ('tt_color', '!=', False),
            ('tt_inventory_number', '!=', False),
        ])
        _log.info("\nORI STOCK MOVE LINES  FOUND:::  %s " % sml_ids)
        for pol in pols:
            ori_lot = ori_lots.filtered(lambda x: x.name == pol.lot_name and x.product_id.id == pol.product_id.id)
            _log.info("\nLOT FOUND:: %s " % ori_lot)
            sml_id = sml_ids.filtered(lambda r: r.lot_id.id == ori_lot.id)
            _log.info("\nSTOCK MOVE LINE ONE FOUND:: %s " % sml_id)
            # BUscar un stock.move.line que tenga como lot_id el que se acaba de encontrar.
            # el stock.move.line ya tiene un picking asociado.
            if not ori_lot:
                continue
            data.append({
                'product_name': ori_lot.product_id.name,
                'serial': ori_lot.name,
                'motor_num': ori_lot.tt_number_motor,
                'color': ori_lot.tt_color,
                'inv_num': ori_lot.tt_inventory_number,
                'aduana': sml_id.picking_id.tt_aduana,
                "aduana_date": sml_id.picking_id.tt_aduana_date_in,
            })
        if len(data) > 0:
            return data
        return False

    def _set_num_pedimento(self):
        # Filter by current company HERE.

        if self.move_type != "out_invoice" or self.state == 'draft':
            return False
        # From sale order
        # if self.invoice_line_ids:
        #     sale_lines = self.invoice_line_ids.sale_line_ids
            # lot_ids = sale_lines.move_ids.filtered(lambda r: r.state == 'done').move_line_ids.mapped('lot_id')
        _log.info("\n Estableciendo número de pedimiento !!")
        # From pos order.
        if self.pos_order_ids:
            for line in self.invoice_line_ids:
                # Cada linea ya tiene una relacion con su linea origen en el punto de venta (pos_order_line_id)
                # cada linea del pos order ya tiene su propio campo de número de serie.
                # Hay que buscar un lot_id original que tenga el mismo nombre
                # Una vez localizado el lot_id, será necesario buscar un aml que use ese serie y que tenga establecido
                # los campos tt. Ese será el picking de la entrada original.

                if not line.pos_order_line_id:
                    continue
                lot_ori_id = self.env['stock.production.lot'].search([
                    ('name', 'in', line.pos_order_line_id.pack_lot_ids.mapped('lot_name'))
                ], limit=1)
                if not lot_ori_id:
                    continue
                sml_ids = self.env['stock.move.line'].search([
                    ('lot_id', '=', lot_ori_id.id),
                    ('state', '=', "done"),
                    ('tt_motor_number', '!=', False),
                    ('tt_color', '!=', False),
                    ('tt_inventory_number', '!=', False),
                ], limit=1)
                if not sml_ids:
                    continue
                _log.info("\n Estableciendo número de pedimiento === %s" % sml_ids.picking_id.tt_num_pedimento)
                line.l10n_mx_edi_customs_number = sml_ids.picking_id.tt_num_pedimento


class AccountMoveLineItt(models.Model):
    _inherit = "account.move.line"

    pos_order_line_id = fields.Many2one('pos.order.line')
