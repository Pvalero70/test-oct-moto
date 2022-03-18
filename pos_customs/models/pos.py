# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_log = logging.getLogger("___name: %s" % __name__)


class PaymentMethodPos(models.Model):
    _inherit = "pos.payment.method"

    payment_method_c = fields.Many2one('l10n_mx_edi.payment.method', string="Forma de pago")


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _order_fields(self, ui_order):
        _log.info(" UI ORDER ==========>>> %s" % ui_order)
        vals = super()._order_fields(ui_order)
        _log.info("1 ========= VALS pos order .. ::: %s " % vals)
        vals['l10n_mx_edi_usage'] = ui_order.get('cfdi_usage')
        _log.info("2 ========= VALS pos order .. ::: %s " % vals)
        # vals['to_invoice'] = True if ui_order.get('to_invoice') else False
        return vals
    
    l10n_mx_edi_usage = fields.Selection(
        selection=[
            ('G01', 'Adquisición de mercancías'),
            ('G02', 'Devoluciones, descuentos o bonificaciones'),
            ('G03', 'Gastos en general'),
            ('I01', 'Construcciones'),
            ('I02', 'Mobilario y equipo de oficina por inversiones'),
            ('I03', 'Equipo de transporte'),
            ('I04', 'Equipo de cómputo y accesorios'),
            ('I05', 'Dados, troqueles, moldes, matrices y herramental'),
            ('I06', 'Comunicaciones telefónicas'),
            ('I07', 'Comunicaciones satelitales'),
            ('I08', 'Otra maquinaria y equipo'),
            ('D01', 'Honorarios médicos, dentales y gastos hospitalarios'),
            ('D02', 'Gastos médicos por incapacidad o discapacidad'),
            ('D03', 'Gastos funerales'),
            ('D04', 'Donativos'),
            ('D05', 'Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación)'),
            ('D06', 'Aportaciones voluntarias al SAR'),
            ('D07', 'Primas por seguros de gastos médicos'),
            ('D08', 'Gastos de transportación escolar obligatoria.'),
            ('D09', 'Depósitos en cuentas para el ahorro, primas que tengan como base planes de pensiones.'),
            ('D10', 'Pagos por servicios educativos (colegiaturas)'),
            ('P01', 'Pör definir'),
        ],
        string="Uso",
        default='P01')

    def _prepare_invoice_vals(self):
        vals = super(PosOrder, self)._prepare_invoice_vals()
        # vals['l10n_mx_edi_payment_method_id'] = self.payment_method_id.l10n_mx_edi_payment_method_id.id
        vals['l10n_mx_edi_usage'] = self.l10n_mx_edi_usage
        # vals['pricelist_id'] = self.pricelist_id
        _log.info("===================== VALORES PARA LA FACTURA... %s" % vals)
        return vals