# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class Purchase(models.Model):

    _inherit = "purchase.order"

    import_xml_cfdi = fields.Many2one("pmg.importa.cfdi.line", string="Cfdi Data")
    file_xml = fields.Binary(string="Cfdi")
    file_name = fields.Char('Nombre archivo', default='cfdi_proveedor.xml')

    def procesa_xml(self, cfdi_line):
        if cfdi_line:
            cfdi_line.leer_archivo()

    def write(self, vals):
        res = super(Purchase, self).write(vals)

        if not self.file_xml and self.import_xml_cfdi:
            self.import_xml_cfdi.unlink()

        if self.file_xml and vals.get('file_xml'):
            
            if self.import_xml_cfdi:
                self.import_xml_cfdi.unlink()
                    
            cfdi_id = self.env['pmg.importa.cfdi.line'].create({
                "file_xml" : self.file_xml
            })
            if cfdi_id:
                _logger.info("####")
                _logger.info("####")
                _logger.info(cfdi_id)
                self.procesa_xml(cfdi_id)
                self.write({"import_xml_cfdi" : cfdi_id, "purchase_id" : res.id})

        return res