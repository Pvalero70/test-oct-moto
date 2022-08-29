# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

# class StockMove(models.Model):
#     _inherit = 'stock.move'

#     def get_inventory_number(self):
#         _logger.info("\n\n ===>> padre original :: %s PADRE: %s Hijos: %s " % (self._origin, self, self.move_line_nosuggest_ids))
#         # Buscamos el último puesto en el wizard (no guardado)
#         mlns_with_inv_num = self.move_line_nosuggest_ids.filtered(lambda x: x.tt_inventory_number_seq is not False)
#         mlns_to_calc = self.move_line_nosuggest_ids.filtered(lambda x: not x.tt_inventory_number_seq)
#         invn_num_self_max = 0
#         # We search in the same document
#         if mlns_with_inv_num:
#             for mlns in mlns_with_inv_num:
#                 invn_num_self_max = mlns.tt_inventory_number_seq if mlns.tt_inventory_number_seq > invn_num_self_max else invn_num_self_max
#         # Buscamos el último guardado.
#         last_ml = self.env['stock.move.line'].search(
#             [('tt_inventory_number_seq', '!=', False), ('company_id', '=', self.company_id.id)],
#             order="tt_inventory_number_seq desc", limit=1)
#         # we search other documents inside.
#         if last_ml:
#             _logger.info("\n\n El mayor de otros documentos :: %s " % last_ml.tt_inventory_number_seq)
#             if invn_num_self_max > last_ml.tt_inventory_number_seq:
#                 # The max seq is in self.
#                 next_seq = invn_num_self_max + 1
#             else:
#                 # Max is in other documents.
#                 next_seq = last_ml.tt_inventory_number_seq + 1
#         else:
#             # Max is in self
#             next_seq = invn_num_self_max + 1

#         # Establecemos el mayor de los dos anteriores + 1 como el que debe establecerse, lo establecemos.
#         for mln in mlns_to_calc:
#             mln.tt_inventory_number_seq = next_seq
#             mln.tt_inventory_number = str(next_seq).zfill(4)
#             next_seq += 1

class StockPicking(models.Model):

    _inherit = 'stock.picking'

    def button_validate(self):
        self.validar_xml_purchase()
        # return
        res = super(StockPicking, self).button_validate()
        return res

    def button_leer_xml(self):

        _logger.info("ENTRA")

        if self.purchase_id.import_xml_cfdi:
            _logger.info("TIENE CFDI")
            xml_compra = self.purchase_id.import_xml_cfdi
            xml_products = self.env['pmg.importa.cfdi.line.product']
            lotes = self.env['stock.production.lot']

            for line in self.move_lines:
                prod = line.product_id
                prods_res = xml_products.search([('line_id', '=', xml_compra.id), ('cfdi_product_id', '=', prod.id)], limit=1)

                line.calc_inv_number()

                _logger.info(line.id)
                if prods_res:
                    created_lots = []
                    for res in prods_res:
                        if res.cfdi_product_chasis and res.cfdi_product_chasis not in created_lots:

                            _logger.info("Intenta crear lote y numero de serie")

                            lote = lotes.create({
                                "name" : res.cfdi_product_chasis,
                                "product_id" : prod.id,
                                "company_id" : self.company_id.id,
                                "tt_number_motor" : res.cfdi_product_numero,
                                "tt_color" : res.cfdi_product_nombre_color,
                                "tt_free_optional" : res.cfdi_product_opcionales
                            })
                            _logger.info("Lote creado..")
                            _logger.info(lote)

                            if lote:

                                created_lots.append(res.cfdi_product_chasis)

                                _logger.info("Intenta crear linea salida..")

                                self.move_line_ids = [(0, 0, {
                                    "lot_id" : lote.id,
                                    "lot_name" : lote.name,
                                    "tt_motor_number" : res.cfdi_product_numero,
                                    "tt_color" : res.cfdi_product_nombre_color,
                                    "tt_free_optional" : res.cfdi_product_opcionales,
                                    "product_id" : prod.id,
                                    "product_uom_id" : 1,
                                    "location_id" : self.location_id.id,
                                    "location_dest_id" : self.location_dest_id.id,
                                    "company_id" : self.company_id.id,
                                    "qty_done" : 1,
                                    "move_id" : line.id,
                                    "picking_id" : self.id
                                })]

                                _logger.info("Created...")

            line.calc_inv_number()
            
        return

    def validar_xml_purchase(self):
        if self.purchase_id.import_xml_cfdi:
            errors = []
            xml_compra = self.purchase_id.import_xml_cfdi
            xml_products = self.env['pmg.importa.cfdi.line.product']

            for line in self.move_lines:
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
                    if not res.cfdi_product_chasis:
                        
                        xml_quantity = res.cfdi_product_qty
                        if int(line.product_uom_qty) != int(xml_quantity):
                            errors.append({
                                "error" : "La cantidad no es igual",
                                "producto" : {
                                    "id" : prod.id,
                                    "sku" : prod.default_code,
                                    "supplier" : res.cfdi_product_clave_prod,
                                    "xml_qty" :  xml_quantity,
                                    "picking_qty" : line.product_uom_qty
                                }
                            })
                            continue

            if errors:
                raise ValidationError(f"No se pudieron validar los datos del CFDI: {errors}")



