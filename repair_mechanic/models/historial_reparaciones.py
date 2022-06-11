import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning

_logger = logging.getLogger(__name__)


class RepairMechanic(models.Model):
    _inherit = 'repair.order'

    product_id = fields.Many2one(
        'product.product', string='Product to Repair',
        domain='_domain_package_type',
        readonly=True, required=True, states={'draft': [('readonly', False)]}, check_company=True)

    #        domain="[('type', 'in', ['product', 'consu']), '|', ('company_id', '=', company_id), ('company_id', '=', False)]",


    def _domain_package_type(self):

        product = self.env['product.product'].search([('type', 'in', ['product', 'consu']), ('company_id', 'in', [self.env.company.id, False])], limit=3)
        _logger.info("Domain %s",product)
        return [('id', 'in', product.ids)]