import logging
from collections import defaultdict


from odoo import _, api, Command, fields, models
from lxml import etree

_logger = logging.getLogger(__name__)


class ResPartnerState(models.Model):
    _inherit = 'res.partner'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ResPartnerState, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                       submenu=submenu)

        doc = etree.XML(res['arch'])
        nodes = doc.xpath("//field[@name='state_id']")
        nodes2 = doc.xpath("//field[@name='email']")

        for node in nodes:
            node.set('options', "{'no_quick_create':True,'no_create_edit':True,'no_open': True,'no_create': True}")

        for node in nodes2:
            _logger.info("Nodo email")
            node.set('attrs', "{}")
            node.set('required', "true")
        res['arch'] = etree.tostring(doc)

        return res

