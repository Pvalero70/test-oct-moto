# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging

_log = logging.getLogger("__--__-->> Seller Commission:: ")

NUM_MONTHS = {
    "1": 'Enero',
    "2": "Febrero",
    "3": "Marzo",
    "4": "Abril",
    "5": "Mayo",
    "6": "Junio",
    "7": "Julio",
    "8": "Agosto",
    "9": "Septiembre",
    "10": "Octubre",
    "11": "Noviembre",
    "12": "Diciembre"
}


class SellerCommission(models.Model):
    _name = "seller.commission"
    _description = "Concentrado de comisiones comisiones de vendedores"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    """
    1 millón de ventas en motocicletas = 4%
    4 millones de ventas en motocicletas = 8%
    Se paga una comisión por moto que está liquidada, siempre y cuando el pedido esté facturado y pagada
    
    En general es necesario agrupar las lineas por categoría, de tal forma que se tenga una linea por categoría y por ende una suma; 
    la regla deberá ir cambiando cuando la linea vaya cambiando su total; 
    
    Por lo anterior, Se debe establecer un constrain en las reglas para que cuando una categoría sea establecida con un método de calculo,
    no pueda ser establecida otra regla con la misma categoría pero con diferente método; es decir: una categoría siempre tendrá un mismo método. 
    """
    name = fields.Char(string="Nombre", compute="compute_name", store=True)
    seller_id = fields.Many2one('res.partner', string="Vendedor", check_company=True)
    mechanic_id = fields.Many2one('repair.mechanic', string="Mecánico")
    company_id = fields.Many2one('res.company', string="Compañía")
    line_ids = fields.One2many('seller.commission.line',
                               'monthly_commission_id',
                               string="Comisiones", tracking=True,
                               help="Lineas de concentrado de sumas, agrupado por categorías. ")
    preline_ids = fields.One2many('seller.commission.preline', 'commission_id', string="Lineas de precalculo", tracking=True)
    amount_total = fields.Float(string="Total de comision", tracking=True)
    state = fields.Selection([
        ('to_pay', "Por pagar"),
        ('paid', "Pagada")], tracking=True, string="Estado")
    payment_date = fields.Datetime(string="Fecha de pago", tracking=True)
    current_month = fields.Selection([
        ("1", 'Enero'),
        ("2", "Febrero"),
        ("3", "Marzo"),
        ("4", "Abril"),
        ("5", "Mayo"),
        ("6", "Junio"),
        ("7", "Julio"),
        ("8", "Agosto"),
        ("9", "Septiembre"),
        ("10", "Octubre"),
        ("11", "Noviembre"),
        ("12", "Diciembre")
    ], string="Mes", tracking=True, required=True)
    commission_quantity_lines = fields.Integer(string="Cantidad de conceptos", tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        coms = super(SellerCommission, self).create(vals_list)
        for com in coms: 
            if not com.company_id:
                com.company_id = self.env.company.id
            if not com.name:
                com.compute_name()
        return coms

    def compute_name(self):
        for reg in self:
            if reg.seller_id:
                reg.name = "%s - %s" % (reg.seller_id.name, NUM_MONTHS[reg.current_month])
            else:
                mechanic_name = "%s" % reg.mechanic_id.first_name
                if reg.mechanic_id.second_name:
                    mechanic_name = mechanic_name+" %s" % reg.mechanic_id.second_name
                if reg.mechanic_id.first_ap:
                    mechanic_name = mechanic_name + " %s" % reg.mechanic_id.first_ap
                if reg.mechanic_id.second_ap:
                    mechanic_name = mechanic_name + " %s" % reg.mechanic_id.second_ap
                reg.name = "%s - %s" % (mechanic_name, NUM_MONTHS[reg.current_month])

    def calc_lines(self):
        """
        Hecha para varios registros. 
        Se crea una linea de comisión en base a la categoría de la pre linea y el hecho de que no tengan una linea asociada, es decir; que no hayan
        usadas ya con anterioridad. 
        """
        _log.info("Calculando lineas con las prelineas")
        rules = self.env['seller.commission.rule'].search([('company_id', '=', self.env.company.id)])
        for reg in self: 
        # iteramos las categorias de las prelineas que no han sido usadas.
            for categ in reg.preline_ids.filtered(lambda pl: not pl.commission_line_id and pl.categ_id).mapped('categ_id'):
                _log.info("Calculando linea para la categoria::: %s (%s) " % (categ, categ.name))
                # Pre lineas a ser sumadas.
                pli = reg.preline_ids.filtered(lambda pl: not pl.commission_line_id and pl.categ_id.id == categ.id)
                plines_amount = sum(pli.mapped('amount'))
                plines_pquantity = sum(pli.mapped('quantity'))
                _log.info("PLINES AMOUNT ::: %s " % plines_amount)

                # Revisamos si tienes una linea previa para esa categoría; si la hay hacemos un update del amount después de
                # sumarle el amount_base y reeconsiderar una nueva regla.
                com_line = reg.line_ids.filtered(lambda li: li.categ_id.id == categ.id)

                if com_line:
                    plines_amount = plines_amount + com_line.amount_base

                rule_id = rules.filtered(lambda ru: (categ.id in ru.product_categ_ids.ids) and (plines_amount >= ru.amount_start))
                _log.info(" CATEGORIAS ESPERADA DE LINEA::: %s   " % rule_id)
                if rule_id:
                    rule_id = rule_id.sorted('amount_start', reverse=True)[0]
                else:
                    _log.error(
                        "No es posible determinar una regla de calculo de comision para esta categoría (%s) de producto." % categ.name)
                    continue
                # Calculamos el nuevo monto de comisión según la regla especifica y el monto base nuevo.
                if rule_id.calc_method in ["percent_utility", "percent_sale"]:
                    # Es un porcentaje de lo que traemos en plines_amount
                    factor = rule_id.amount_factor/100
                    line_amount = plines_amount*factor
                else:
                    # Monto fijo: el monto fijado en la regla es lo que se paga por cada una de las ventas realizadas
                    line_amount = rule_id.amount_factor*plines_pquantity

                if com_line:
                    # Existe una linea para esa categoría. hacemos update.
                    com_line.write({
                        'amount': com_line.amount+line_amount if rule_id.calc_method == "fixed" else line_amount,
                        'amount_base': plines_amount,
                        'comm_rule': rule_id.id,
                        'commission_date': fields.Datetime.now()
                    })
                    self.env.cr.commit()
                    for pl in pli:
                        pl.commission_line_id = com_line.id
                else:
                    # No existe una linea para esa categoría; la creamos.
                    com_line = self.env['seller.commission.line'].create({
                        'monthly_commission_id': reg.id,
                        'amount': line_amount,
                        'amount_base': plines_amount,
                        'comm_rule': rule_id.id,
                        'commission_date': fields.Datetime.now(),
                        'categ_id': categ.id
                    })
                    for pl in pli:
                        pl.commission_line_id = com_line.id
            reg.amount_total = sum(reg.line_ids.mapped('amount'))


class SellerCommissionLine(models.Model):
    _name = "seller.commission.line"
    _description = "Comisiones de vendedor por mes"
    """
    Tabla de acumulados, es calculada en base en la información en la tabla de concentrados, en donde se suman por categoría. 

    Esta tabla concentra la sumatoria del total de varias lineas de varias facturas; siempre que sean de la misma categoría; para cada comisión de cada vendedor.
    Por lo tanto la información de las facturas consideradas no podrían ser aquí. 
    """

    monthly_commission_id = fields.Many2one('seller.commission', string="Comision mensual", help="Acumulado mensual")
    name = fields.Char(string="Nombre", compute="_compute_name")
    # seller_id = fields.Many2one('res.partner', related="monthly_commission_id.seller_id")
    # mechanic_id = fields.Many2one('repair.mechanic', related="monthly_commission_id.mechanic_id")
    amount = fields.Float(string="Total de comisión", help="Total a pagar por ésta comisión en determinada categoría de producto.")
    amount_base = fields.Float(string="Monto base ", help="El monto base del cual se calculará la comisión. ")
    commission_date = fields.Datetime(string="Hora de comisión")
    comm_rule = fields.Many2one('seller.commission.rule', string="Regla de calculo")
    categ_id = fields.Many2one('product.category', string="Categoria de producto")

    def _compute_name(self):
        for reg in self:
            reg.name = "%s-%s" % (reg.categ_id.name, reg.amount)


class SellerCommissionPreline(models.Model):
    _name = "seller.commission.preline"
    _description = "Lineas que serán consideradas para crear los acumulados"
    """
    A partir de ésta tabla se generan las lineas de comisión, aquí será el acumulado; cada que se modifique o se cree un registro aquí 
    """

    amount = fields.Float(string="Total a comisionar")
    categ_id = fields.Many2one('product.category', string="Categoria de producto")
    invoice_id = fields.Many2one('account.move', string="Factura")
    commission_id = fields.Many2one('seller.commission', string="Comisión relacionada")
    commission_line_id = fields.Many2one('seller.commission.line', string="linea de comisión", help="Linea de la comisión en la que se sumó. Una linea por factura.")
    quantity = fields.Float(string="Cantidad de productos")


class SellerCommissionRule(models.Model):
    _name = "seller.commission.rule"
    _description = "Reglas de calculo para comisiones de vendedores."

    name = fields.Char(string="Nombre", compute="_compute_rule_name", store=False)
    calc_method = fields.Selection([('fixed', 'Monto fijo'),
                                    ('percent_utility', '% Utilidad'),
                                    ('percent_sale', '% Venta')], string="Método", required=True)
    company_id = fields.Many2one('res.company', string="Compañía", default=lambda self: self.env.company)
    product_categ_ids = fields.Many2many('product.category', string="Categorías de productos", required=True)
    amount_factor = fields.Float(string="Factor")
    amount_start = fields.Float(string="A partir de ($)", help="A Partir de esta cantidad entra esta regla. Si se configura como cero se considera monto libre.")

    # @api.onchange('calc_method', 'amount_factor')
    def _compute_rule_name(self):
        for reg in self:
            if not reg.calc_method or not reg._origin:
                continue
            method = {
                'fixed': 'Monto fijo',
                'percent_utility': '% Utilidad',
                'percent_sale': '% Venta',
            }
            rule_name = "%s %s - %s" % (method[reg.calc_method], reg.amount_factor, reg.id)
            reg.name = rule_name

    @api.constrains('calc_method', 'product_categ_ids')
    def check_commission_rules_categ(self):
        """
        Método que revisa que las categorías establecidas en dicho registro no sean
        encontradas en otras reglas con un método de calculo diferente;
        :return:
        """
        def sublista(l1, l2):
            # Regresa los elementos de la primer lista que están en la segunda.
            return [x for x in l1 if x in l2]
        other_rules = self.env['seller.commission.rule'].search([
            ('company_id', '=', self.company_id.id),
            ('calc_method', '!=', self.calc_method),
        ]).filtered(lambda r: len(sublista(self.product_categ_ids, r.product_categ_ids)) > 0)
        if other_rules:
            raise ValidationError(_("Las reglas %s entran en conflicto con la regla que está intentando crear o editar,"
                                    " ya que algunas de sus categorías de productos que intenta poner en la regla que"
                                    " está editando o creando se encuentran en dichas reglas con conflicto pero con"
                                    " diferente método de calculo." % other_rules.mapped('name')))


