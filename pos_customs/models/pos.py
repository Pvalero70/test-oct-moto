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
            _log.info("\n\n VALS CUSTOM POS FOR INVOICE:: %s " % vals_pos)
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
        # OJO, despues de ésta linea dice que ando intentando conciliar asientos ya conciliados.
        _log.info("\n\n2) Preparando los valores del uso del CFDI:::  %s " % self.l10n_mx_edi_usage)
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
        """
        _log.info(" DIVIDIENDO FACTURA.. invoice data:: %s" % invoice_data)
        # Get payment methods with bank commission.
        payment_bc_used_ids = order.payment_ids.filtered(lambda pa: pa.payment_method_id.bank_commission_method != False)
        ori_invoice_lines = invoice_data['invoice_line_ids']
        # Avoid make two invoices when there isn't bc
        if not payment_bc_used_ids and quit_commissions:
            return invoice_data
        if not payment_bc_used_ids and not quit_commissions:
            return False
        product_bc_ids = payment_bc_used_ids.mapped('payment_method_id').mapped('bank_commission_product_id')
        new_invoice_line_ids = []
        is_commission_invoice = False
        for ori_line in ori_invoice_lines:
            line_product_id = ori_line[2]['product_id']
            is_bc = True if line_product_id in product_bc_ids.ids else False
            if is_bc and not quit_commissions:
                new_invoice_line_ids.append(ori_line)
                is_commission_invoice = True
            if not is_bc and quit_commissions:
                new_invoice_line_ids.append(ori_line)
        if len(new_invoice_line_ids) > 0:
            invoice_data['invoice_line_ids'] = new_invoice_line_ids
        if is_commission_invoice:
            _log.info("ES COMISSION...  =P ")
            first_product_category = product_bc_ids[0].categ_id
            pc_loc_src_id = order.config_id.picking_type_id.default_location_src_id
            domain = [('company_id', '=', self.company_id.id),
                      ('c_location_id', '=', pc_loc_src_id.id)
                      ]
            journal_ids = self.env['account.journal'].search(domain)
            journal_id = journal_ids.filtered(lambda jo: first_product_category.id in jo.c_product_category_ids.ids)
            # Como el diario se escogería en base a la caterogía del producto y el punto de venta (ubicación) no
            # importa el método que usen; basta con que alguno de los productos asiciados como comisión al metodo de pago
            # pueda relacionar un diario y a ese se asigna la comisión.
            # La catagoría del producto puede ser la padre.
            if journal_id:
                invoice_data['journal_id'] = journal_id[:1].id
            elif first_product_category.parent_id:
                journal_id = journal_ids.filtered(
                    lambda jo: first_product_category.parent_id.id in jo.c_product_category_ids.ids)
                if journal_id:
                    invoice_data['journal_id'] = journal_id[:1].id
            else:
                # Por defauilt dejamos el diario que tiene el método de
                payment_method_com_id = payment_bc_used_ids.mapped('payment_method_id')[0]
                invoice_data['journal_id'] = payment_method_com_id.bc_journal_id.id
        return invoice_data

    def commission_line_exists(self, invoice_data, order=None):
        ori_invoice_lines = invoice_data['invoice_line_ids']
        payment_bc_used_ids = order.payment_ids.filtered(
            lambda pa: pa.payment_method_id.bank_commission_method != False)
        product_bc_ids = payment_bc_used_ids.mapped('payment_method_id').mapped('bank_commission_product_id')
        is_commission_invoice = False
        for ori_line in ori_invoice_lines:
            line_product_id = ori_line[2]['product_id']
            is_bc = True if line_product_id in product_bc_ids.ids else False
            if is_bc:
                is_commission_invoice = True
        return is_commission_invoice

    def _apply_invoice_payments_bc(self, invoice, order):
        _log.info(" APPLY PAYMENTS ...    for order and invoices xD. ")
        _log.info(" APLICANDO PAGOUS.. ")
        receivable_account = self.env["res.partner"]._find_accounting_partner(self.partner_id).property_account_receivable_id
        payment_moves = order.payment_ids.mapped('account_move_id')
        for pay in payment_moves:
            _log.info("payment :: %s " % pay)
        invoice_receivable = invoice.line_ids.filtered(lambda line: line.account_id == receivable_account)
        if not invoice_receivable.reconciled and receivable_account.reconcile:
            payment_receivables = payment_moves.mapped('line_ids').filtered(lambda line: line.account_id == receivable_account and line.reconciled is False)
            for pa in payment_receivables:
                _log.info("PAGOS ::: %s  account move: %s reconcilied::: %s " % (pa, pa.move_id, pa.reconciled))

            (invoice_receivable | payment_receivables).reconcile()

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
            _log.info("MOVE VALSSSS 1 :: %s " % move_vals)

            comm_line_exists = self.commission_line_exists(move_vals, order=order)
            if comm_line_exists:
                move_vals_commissions = move_vals.copy()
                move_vals_commissions = self._split_invoice_vals_bk(move_vals_commissions, quit_commissions=False, order=order)
                move_vals = self._split_invoice_vals_bk(move_vals, quit_commissions=True, order=order)
                _log.info("MOVE VALSSSS 2 :: %s" % move_vals)
                _log.info(" MOVE VALS COMMM ::: %s " % move_vals_commissions)
                new_move_bc = None
                if move_vals_commissions:
                    new_move_bc = order._create_invoice(move_vals_commissions)
                    _log.info(" FACTURA POR COMISION ::::: %s " % new_move_bc)
                    new_move_bc.sudo().with_company(order.company_id)._post()
                    moves += new_move_bc
# Comentado por pruebas.
            _log.info(" Try to create invoice")
            new_move = order._create_invoice(move_vals)
            _log.info(" LA FACTURA NORMAL ::: %s " % new_move)
            order.write({'account_move': new_move.id, 'state': 'invoiced'})
            new_move.sudo().with_company(order.company_id)._post()
            moves += new_move
            line_zerodays = new_move.invoice_payment_term_id.line_ids.filtered(lambda x: x.value_amount == 0 and x.days == 0 and x.option == "day_after_invoice_date")
            if line_zerodays:
                order._apply_invoice_payments()
            else:
                delta_days = new_move.invoice_payment_term_id.line_ids.filtered(lambda x: x.days > 0 and x.option == "day_after_invoice_date")[:1].days
                new_move.invoice_date_due = fields.Date.today() + relativedelta(days=delta_days)
                new_move._compute_l10n_mx_edi_payment_policy()
            if comm_line_exists and new_move_bc is not None:
                _log.info(" APLICANDO PAGOS PARA :: %s " % new_move_bc)
                self._apply_invoice_payments_bc(new_move_bc, order=order)

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

    @api.model
    def create_comm_inv_pos(self, pon=None):
        if pon is None:
            return {}
        poso_domain = [('pos_reference', '=ilike', pon)]
        poso = self.env['pos.order'].search(poso_domain, limit=1)
        if len(poso.lines) != 1:
            return {}
        product_comm_payment_method = poso.payment_ids.mapped('payment_method_id').filtered(lambda pm: pm.bank_commission_method != False and pm.bank_commission_product_id != False)
        if not product_comm_payment_method:
            return {}
        comm_product_id = product_comm_payment_method.bank_commission_product_id
        if poso.lines[0].product_id.id != comm_product_id.id:
            return {}
        poso_inv = poso.action_pos_order_invoice()
        if poso_inv:
            return poso_inv
        return {}