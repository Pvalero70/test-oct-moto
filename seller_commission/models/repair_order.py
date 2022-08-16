# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging

_log = logging.getLogger("---__--__-···>> REPARATION ORDER Seller Commission:: ")


class RepairOrderSc(models.Model):
    _inherit = 'repair.order'

    def create_commission(self, invoice=None):
        """
        Método que crea una o varias comisiones a partir de un pedido de reparacion 
        """
        if self.operations and len(self.operations) > 0:
            seller_commission_id = self.make_prelines_seller(invoice)

        if self.fees_lines and len(self.fees_lines) > 0:
            mechanic_commission_id = self.make_prelines_mechanic(invoice)
        

    def make_prelines_seller(self, invoice=None):
        """
        Realiza prelineas en una comisión del vendedor de piezas en una orden de reparación.
        """
        # COMISIONES AL VENDEDOR.

        product_categs = self.operations.mapped('product_id').mapped('categ_id').mapped('parent_id')
        if not product_categs:
            return False
        all_company_rules = self.env['seller.commission.rule'].search([('company_id', '=', self.company_id.id)])
        _log.info("REGLAS DE COMPAÑIA :: %s " % all_company_rules)
        if not all_company_rules:
            return False
        prelines = []
        for line in self.operations:
            # line_rules = all_company_rules.filtered(lambda ru: line.product_id.categ_id.parent_id.id in all_company_rules.ids)
            # if not line_rules:
            #     continue
            # line_comm_method = line_rules.mapped('calc_method')
            # Estas lineas no manejan margen de ganancia. No debe considerarse la categoría margen de ganancia para
            # estas piezas. 
            # Revisando la categoría.
            line_categ = line.product_id.categ_id.parent_id
            if not line_categ:
                line_categ = line.product_id.categ_id
            preline = {
                'amount': line.price_subtotal,
                'categ_id': line_categ.id,
                'invoice_id': invoice.id,
                'quantity': line.product_uom_qty
            }
            _log.info(" SELLER INFO PRELINEA A CREAR ::: %s " % preline)
            prelines.append((0, 0, preline))
        # Buscamos la última comisión que esté sin pagar para dicho vendedor.
        commission = self.env['seller.commission']
        commission_ids = commission.search([
            ('seller_id', '=', self.user_id.partner_id.id),
            ('state', '=', "to_pay")
        ], order="current_month desc")
        if commission_ids:
            commission_id = commission_ids[0]
            _log.info("COMISION ENCONTRADA:: %s " % commission_id)
        else:
            # Creamos uno nuevo.
            commission_id = commission.create({
                'seller_id': self.user_id.partner_id.id,
                'current_month': str(fields.Date().today().month),
                'state': "to_pay"
            })
            _log.info(" COMISION creada :: %s " % commission_id)
        commission_id.preline_ids = prelines
        commission_id.calc_lines()


    def make_prelines_mechanic(self, invoice=None):
        """
        Realiza las prelinas de una comisión de mecánico en una orden de reparación. 
        """
        # COMISIONES AL MECÁNICO.
        _log.info("Haciendo prelineas para .. ")
        product_categs = self.fees_lines.mapped('product_id').mapped('categ_id').mapped('parent_id')
        if not product_categs:
            product_categs = self.fees_lines.mapped('product_id').mapped('categ_id')
            if not product_categs:
                return False
        all_company_rules = self.env['seller.commission.rule'].search([('company_id', '=', self.company_id.id)])
        _log.info("REGLAS DE COMPAÑIA :: %s " % all_company_rules)
        if not all_company_rules:
            return False
        prelines = []
        for line in self.fees_lines:
            # line_rules = all_company_rules.filtered(lambda ru: line.product_id.categ_id.parent_id.id in all_company_rules.ids)
            # if not line_rules:
            #     continue
            # line_comm_method = line_rules.mapped('calc_method')
            # Estas lineas no manejan margen de ganancia. No debe considerarse la categoría margen de ganancia para
            # estas piezas. 
            # Revisando la categoría. 
            preline = {
                'amount': line.price_subtotal,
                'categ_id': line.product_id.categ_id.id,
                'invoice_id': invoice.id,
                'quantity': line.product_uom_qty
            }
            _log.info(" MECHANIC INFO PRELINEA A CREAR ::: %s " % preline)
            prelines.append((0, 0, preline))
        # Buscamos la última comisión que esté sin pagar para dicho vendedor.
        if len(prelines) > 0:
            commission = self.env['seller.commission']
            commission_ids = commission.search([
                ('mechanic_id', '=', self.mechanic_id.id),
                ('state', '=', "to_pay")
            ], order="current_month desc")
            if commission_ids:
                commission_id = commission_ids[0]
                _log.info("COMISION ENCONTRADA:: %s " % commission_id)
            else:
                # Creamos uno nuevo.
                commission_id = commission.create({
                    'mechanic_id': self.mechanic_id.id,
                    'current_month': str(fields.Date().today().month),
                    'state': "to_pay"
                })
                _log.info(" COMISION creada :: %s " % commission_id)
            commission_id.preline_ids = prelines
            commission_id.calc_lines()
            return commission_id
            _log.info("COMISION MECANICO ::: %s " % commission_id)
        else:
            return False