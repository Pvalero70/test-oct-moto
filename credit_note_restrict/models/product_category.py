# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning
import xml.etree.ElementTree as etree

_logger = logging.getLogger(__name__)


class ResUserInheritDiscount(models.Model):
    _inherit = 'product.category'

    account_credit_note_id = fields.Many2one('account.account',"Cuenta de nota de credito")
    account_discount_id = fields.Many2one('account.account', "Cuenta de descuento o devolucion")



class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        _logger.info("ACCOUNT MOVE MODEL:: view_type:%s",view_type)
        res = super(AccountMoveInherit, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                  toolbar=toolbar, submenu=submenu)
        _logger.info("ACCOUNT MOVE MODEL:: view type %s,permiso factura client %s,  es out invoice %s",view_type, self.env.user.has_group('credit_note_restrict.factura_client_group'), self.move_type == 'out_invoice')
        doc = etree.XML(res['arch'])
        if view_type == 'form' and self.env.user.has_group('credit_note_restrict.factura_client_group') and self.move_type == 'out_invoice':
            for node_form in doc.xpath("//form"):
                _logger.info("ACCOUNT MOVE MODEL:: create = false")
                node_form.set("create", 'false')
        res['arch'] = etree.tostring(doc)
        return res