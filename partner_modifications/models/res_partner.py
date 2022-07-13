import logging
from collections import defaultdict


from odoo import _, api, Command, fields, models
from lxml import etree
from odoo.exceptions import ValidationError, UserError, Warning


_logger = logging.getLogger(__name__)


class ResPartnerName(models.Model):
    _inherit = 'res.partner'

    first_name = fields.Char(string="Primer nombre")
    second_name = fields.Char(string="Segundo nombre")
    first_ap = fields.Char(string="Primer Apellido")
    second_ap = fields.Char(string="Segundo Apellido")
    #type_rfc = fields.Selection([
    #    ("general", "Publico General"),
    #    ("fiscal", "Cliente Fiscal")
    #], string="Tipo de RFC")
    rfc_general = fields.Selection([
        ("XAXX010101000", "XAXX010101000"),
    ], string="RFC")

    @api.onchange('rfc_general')
    def _vat_general(self):
        if self.rfc_general:
            self.vat = self.rfc_general
        else:
            self.vat = ''


    @api.onchange('first_name', 'second_name','first_ap','second_ap')
    def _compute_name_person(self):
        _logger.info("Ejecutamos on change")
        nombre_completo = ''
        if self.first_name:
            nombre_completo += self.first_name + " "
        if self.second_name:
            nombre_completo += self.second_name + " "
        if self.first_ap:
            nombre_completo += self.first_ap + " "
        if self.second_ap:
            nombre_completo += self.second_ap + " "
        self.name = nombre_completo

        partners = self.env['res.partner'].search([('name', '=',nombre_completo)])
        if len(partners) > 0:
            raise ValidationError(_('Advertencia!, Ya existe un cliente con el nombre %s.', nombre_completo))



