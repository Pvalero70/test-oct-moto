# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning
from lxml import etree

### notas de credito en contabilidad
_logger = logging.getLogger(__name__)


class RepairOrderButtonInherit(models.Model):
    _inherit = 'repair.order'

    create_invoice_permited = fields.Boolean(string="Permiso para ver el boton CREAR FACTURA", compute='get_user')

    @api.depends('create_invoice_permited')
    def get_user(self):

        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        if res_user.has_group('credit_note_restrict.button_create_inv_repair_group'):
            self.create_invoice_permited = True
        else:
            self.create_invoice_permited = False