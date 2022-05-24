import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning

_logger = logging.getLogger(__name__)


class RepairMechanic(models.Model):
    _name = 'repair.mechanic'

    _description = "Model that saves contact of mechanics"
    _rec_name = 'name_computed'


    name_computed = fields.Char(string="Computado", compute='_compute_name',store=True)

    first_name = fields.Char("Primer nombre",required=1)
    second_name = fields.Char("Segundo nombre")
    first_ap = fields.Char("Primer apellido", required=1)
    second_ap = fields.Char("Segundo apellido")
    numero_mecanico = fields.Char("Numero de tecnico", compute='_compute_num_tecnico', store=True)
    location_id = fields.Many2one('stock.location',"Sucursal")
    company_id = fields.Many2one('res.company',"Empresa",default=lambda self: self.env.company)

    @api.depends('first_name')
    def _compute_num_tecnico(self):
        if self.id:

            mecanico_lines = self.env['repair.mechanic'].search([('company_id', '=', self.company_id.id), ('id', '!=', self.id)])
            arr = [mec.numero_mecanico for mec in mecanico_lines]

            _logger.info("REPAIR MECHANIC::Valores encontrados = %s, array valores = %s,company activa = %s ",mecanico_lines,arr,self.company_id.name)
            if len(mecanico_lines) == 0:
                self.numero_mecanico = str(1).zfill(3)
            else:
                max_val = max(arr)
                _logger.info("REPAIR MECHANIC::Valor maximo = %s", max_val)
                self.numero_mecanico = str(int(max_val) + 1).zfill(3)




    @api.depends('first_name','second_name','first_ap','second_ap')
    def _compute_name(self):
        for rec in self:
            nombre = ''
            if rec.first_name:
                nombre = rec.first_name + " "

            if rec.second_name:
                nombre += rec.second_name + " "

            if rec.first_ap:
                nombre += rec.first_ap + " "

            if rec.second_ap:
                nombre+= rec.second_ap


            rec.name_computed = nombre


class RepairOrderInherit(models.Model):

    _inherit = 'repair.order'

    mechanic_id = fields.Many2one('repair.mechanic',"Mecanico")


