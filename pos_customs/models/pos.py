# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import logging
_log = logging.getLogger("___name: %s" % __name__)


class PaymentMethodPos(models.Model):
    _inherit = "pos.payment.method"

    payment_method_c = fields.Many2one('l10n_mx_edi.payment.method', string="Forma de pago")


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _order_fields(self, ui_order):
        vals = super()._order_fields(ui_order)
        vals_pos = ui_order.get('to_invoice')
        if isinstance(vals_pos, list):
            vals['l10n_mx_edi_usage'] = vals_pos[0]
            vals['cfdi_payment_term_id'] = vals_pos[1]
        vals['to_invoice'] = True if ui_order.get('to_invoice') else False
        return vals

    salesman_id = fields.Many2one('res.users', string="Ejecutivo", compute="_compute_salesman", store=True)
    cfdi_payment_term_id = fields.Many2one('account.payment.term', 'Terminos de pago')
    payment_method_id = fields.Many2one('pos.payment.method', "Metodo de Pago", compute="get_payment_method",
                                        store=True)
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

    @api.depends('payment_ids')
    def get_payment_method(self):
        for rec in self:
            formas = {}
            for pay in rec.payment_ids:
                formas[pay.payment_method_id.id] = formas.get(pay.payment_method_id.id, 0) + pay.amount
            met = sorted(formas.items(), key=lambda x: x[1])
            rec.payment_method_id = met[0] if met else False

    def _prepare_invoice_vals(self):
        vals = super(PosOrder, self)._prepare_invoice_vals()
        vals['l10n_mx_edi_payment_method_id'] = self.payment_method_id.payment_method_c.id
        vals['l10n_mx_edi_usage'] = self.l10n_mx_edi_usage
        vals['invoice_payment_term_id'] = self.cfdi_payment_term_id.id

        return vals

    @api.model
    def _split_invoice_vals_bk(self, invoice_data, quit_commissions=True, order=None):
        """
        This method process invoice data to generate two different sets; one for common lines and other for
        lines that have bank commission products.
        :param invoice_data: the original dataset
        :param quit_commissions: to decide which lines must be removed. By default quit the bank commission lines.
        :param order: pos order object.
        :return: invoice data set without some lines, depends of  quit_commissions

        Ejemplo de invoice data:
                    {
                    'invoice_origin': 'Lopez Mateos/0011',
                    'journal_id': 32,
                    'move_type': 'out_invoice',
                    'ref': 'Lopez Mateos/0011',
                    'partner_id': 11,
                    'partner_bank_id': False,
                    'currency_id': 33,
                    'invoice_user_id': 2,
                    'invoice_date': datetime.date(2022, 5, 18),
                    'fiscal_position_id': False,
                    'invoice_line_ids':
                        [
                        (0, None, {
                            'product_id': 210,
                            'quantity': 1.0,
                            'discount': 0.0,
                            'price_unit': 500.0,
                            'name': 'BALATA',
                            'tax_ids': [(6, 0, [14])],
                            'product_uom_id': 1,
                            'pos_order_line_id': 21
                            }),
                        (0, None, {
                            'product_id': 219,
                            'quantity': 1.0,
                            'discount': 0.0,
                            'price_unit': 35.0,
                            'name': 'Comisión por uso de tarjeta',
                            'tax_ids': [(6, 0, [])],
                            'product_uom_id': 1,
                            'pos_order_line_id': 22
                            })
                        ],

                    'invoice_cash_rounding_id': False,
                    'team_id': crm.team(5,),
                    'partner_shipping_id': 11,
                    'l10n_mx_edi_payment_method_id': 18,
                    'l10n_mx_edi_usage': 'P01',
                    'invoice_payment_term_id': '1'

                    }

        """
        # Get payment methods with bank commission.
        payment_bc_used_ids = order.payment_ids.filtered(lambda pa: pa.payment_method_id.bank_commission_method != False)
        ori_invoice_lines = invoice_data['invoice_line_ids']

        if not payment_bc_used_ids:
            return invoice_data
        product_bc_ids = payment_bc_used_ids.mapped('payment_method_id').mapped('bank_commission_product_id')
        new_invoice_line_ids = []
        # quitamos las lineas de comisiones de invoice data.
        # Iterate ori invoice lines, copy in a new array lines.
        # search each line and find the line product in payment metho
        for ori_line in ori_invoice_lines:
            line_product_id = ori_line[2]['product_id']
            is_bc = True if line_product_id in product_bc_ids.ids else False
            if is_bc and not quit_commissions:
                # Dejamos comisiones.
                new_invoice_line_ids.append(ori_line)
            if not is_bc and quit_commissions:
                # Dejamos lineas que no son comision.
                new_invoice_line_ids.append(ori_line)
        if len(new_invoice_line_ids) > 1:
            invoice_data['invoice_line_ids'] = new_invoice_line_ids
        return invoice_data

    def _generate_pos_order_invoice(self):
        moves = self.env['account.move']

        for order in self:
            # Force company for all SUPERUSER_ID action
            if order.account_move:
                moves += order.account_move
                continue

            if not order.partner_id:
                raise UserError(_('Please provide a partner for the sale.'))
            move_vals = order._prepare_invoice_vals()
            # La idea es facturar por separado, creamos una copia de move_vals y
            # al original le quitamos la o las lineas con algún producto que
            move_vals_commissions = self._split_invoice_vals_bk(move_vals, quit_commissions=False, order=order)
            move_vals = self._split_invoice_vals_bk(move_vals, quit_commissions=True, order=order)



# Comentado por pruebas.
            new_move = order._create_invoice(move_vals)
            new_move_bc = order._create_invoice(move_vals_commissions)

            _log.info("\n Factura SIN comision:: %s \n Factura CON comision :: %s " % (new_move, new_move_bc))

            order.write({'account_move': new_move.id, 'state': 'invoiced'})
            new_move.sudo().with_company(order.company_id)._post()
            new_move_bc.sudo().with_company(order.company_id)._post()
            moves += new_move
            line_zerodays = new_move.invoice_payment_term_id.line_ids.filtered(lambda x: x.value_amount == 0 and x.days == 0 and x.option == "day_after_invoice_date")
            if line_zerodays:
                order._apply_invoice_payments()
            else:
                delta_days = new_move.invoice_payment_term_id.line_ids.filtered(lambda x: x.days > 0 and x.option == "day_after_invoice_date")[:1].days
                new_move.invoice_date_due = fields.Date.today() + relativedelta(days=delta_days)
                new_move._compute_l10n_mx_edi_payment_policy()

            # Ya creada la factura de comisiones, aplicar las mismas validaciones anterires que aplican a la factura convencional.

        if not moves:
            return {}

        return {
            'name': _('Customer Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': moves and moves.ids[0] or False,
        }

    @api.depends('lines.sale_order_origin_id')
    def _compute_salesman(self):
        for posord in self:
            if posord.lines:
                sale_order = posord.lines.filtered(lambda l: l.sale_order_origin_id is not False).mapped('sale_order_origin_id')[:1]
                if sale_order:
                    posord.salesman_id = sale_order.user_id.id
                else:
                    posord.salesman_id = False
            else:
                posord.salesman_id = False

