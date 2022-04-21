# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


class PosOrderC(models.Model):
    _inherit = "pos.order"

    def _prepare_invoice_vals(self):
        vals = super(PosOrderC, self)._prepare_invoice_vals()
        if not self.lines:
            return vals
        first_product_category = self.lines[:1].product_id.categ_id
        pc_loc_src_id = self.config_id.picking_type_id.default_location_src_id

        # Search journal by product category, location source and company.
        # UPDATE: the category field in journal has been changed to m2m field.
        domain = [('company_id', '=', self.company_id.id),
                  ('c_location_id', '=', pc_loc_src_id.id)
                  ]
        journal_ids = self.env['account.journal'].search(domain)
        if not journal_ids:
            return vals

        # Filter the journals by product category in first_product_category.
        journal_id = journal_ids.filtered(lambda jo: first_product_category.id in jo.c_product_category_ids.ids)
        # If the journal was found, set it.
        if journal_id:
            vals['journal_id'] = journal_id.id
        elif first_product_category.parent_id:
            journal_id = journal_ids.filtered(lambda jo: first_product_category.parent_id.id in jo.c_product_category_ids.ids)
            if journal_id:
                vals['journal_id'] = journal_id.id

        return vals
