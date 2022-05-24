# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import logging
_log = logging.getLogger("___name: %s" % __name__)


class PosOrderTt(models.Model):
    _inherit = "pos.order"

    def _prepare_invoice_line(self, order_line):
        res = super(PosOrderTt, self)._prepare_invoice_line(order_line)
        if self.env.company.restrict_inv_sn_flow:
            return res
        if 'pos_order_line_id' not in res:
            res['pos_order_line_id'] = order_line.id
        # _log.info("\nPREPARANDO LINEA:: %s " % res)
        lot_ori_id = self.env['stock.production.lot'].search([
            ('name', 'in', order_line.pack_lot_ids.mapped('lot_name'))
        ], limit=1)
        if lot_ori_id:
            sml_ids = self.env['stock.move.line'].search([
                ('lot_id', '=', lot_ori_id.id),
                ('state', '=', "done"),
                ('tt_motor_number', '!=', False),
                ('tt_color', '!=', False),
                ('tt_inventory_number', '!=', False),
            ], limit=1)
            if sml_ids:
                res['l10n_mx_edi_customs_number'] = sml_ids.picking_id.tt_num_pedimento
        return res
