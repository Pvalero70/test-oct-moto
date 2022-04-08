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
        domain = [('company_id', '=', self.company_id.id),
                  ('c_product_category_id', '=', first_product_category.id),
                  ('c_location_id', '=', pc_loc_src_id.id)
                  ]
        journal_id = self.env['account.journal'].search(domain, limit=1)

        # If the journal was found, set it.
        if journal_id:
            vals['journal_id'] = journal_id.id
        elif first_product_category.parent_id:
            # If the journal wasn't found, search using the parent category, if exists.
            domain = [('company_id', '=', self.company_id.id),
                      ('c_product_category_id', '=', first_product_category.parent_id.id),
                      ('c_location_id', '=', pc_loc_src_id.id)
                      ]
            journal_id = self.env['account.journal'].search(domain, limit=1)
            if journal_id:
                vals['journal_id'] = journal_id.id

        return vals
