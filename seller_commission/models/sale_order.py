# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging

_log = logging.getLogger("\n\n---___---___--__-···>> Seller Commission:: ")


class SaleOrderSc(models.Model):
    _inherit = "sale.order"

    def create_commission(self, invoice=None, order=None):
        """
        Método que crea una comisión sobre el vendedor de esta orden, o bien se suma a una comisión ya hecha. 
        """
        _log.info("Creando comisión de vendedor")

        # Iteramos sobre las lineas y vemos que peps. 
        
