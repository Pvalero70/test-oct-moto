# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):

    _inherit = 'stock.picking'

    def button_validate(self):
        self.validar_xml_purchase()
        return
        # res = super(StockPicking, self).button_validate()
        # return res

    def validar_xml_purchase(self):
        if self.purchase_id.import_xml_cfdi:
            errors = []
            xml_compra = self.purchase_id.import_xml_cfdi
            xml_products = self.env['pmg.importa.cfdi.line.product']
            lotes = self.env['stock.production.lot']

            for line in self.move_ids_without_package:
                prod = line.product_id
                res = xml_products.search([('line_id', '=', xml_compra.id), ('cfdi_product_id', '=', prod.id)], limit=1)

                if not res:
                    errors.append({
                        "error" : "El producto no se encontro en el XML",
                        "producto" : {
                            "id" : prod.id,
                            "sku" : prod.default_code
                        }
                    })
                    continue

                if res:
                    xml_quantity = res.cfdi_product_qty
                    if int(line.quantity_done) != int(xml_quantity):
                        errors.append({
                            "error" : "La cantidad no es igual",
                            "producto" : {
                                "id" : prod.id,
                                "sku" : prod.default_code,
                                "supplier" : res.cfdi_product_clave_prod,
                                "xml_qty" :  xml_quantity,
                                "picking_qty" : line.quantity_done
                            }
                        })
                        continue
                lote = lotes.search([('name', '=', res.cfdi_product_chasis)])
                if lote:
                    line.move_line_nosuggest_ids = (0, 0, {
                        "lot_id" : lote.id,
                        "tt_motor_number" :  res.cfdi_product_numero,
                        "tt_color" : res.cfdi_product_nombre_color
                    })

            if errors:
                raise ValidationError(f"No se pudieron validar los datos del CFDI: {errors}")



