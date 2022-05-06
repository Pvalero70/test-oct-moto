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
        if 'pos_order_line_id' not in res:
            res['pos_order_line_id'] = order_line.id
        _log.info("\nPREPARANDO LINEA:: %s " % res)
        return res
