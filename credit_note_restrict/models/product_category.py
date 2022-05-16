# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning
# import xml.etree.ElementTree as etree
from lxml import etree

_logger = logging.getLogger(__name__)

class ResUserInheritDiscount(models.Model):
    _inherit = 'product.template'

    is_discount_product = fields.Boolean("Es producto descuento",default=False)


class ResUserInheritDiscount(models.Model):
    _inherit = 'product.category'

    account_credit_note_id = fields.Many2one('account.account', "Cuenta de devolucion")
    account_discount_id = fields.Many2one('account.account', "Cuenta de descuento o bonificacion")


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountMoveInherit, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                              toolbar=toolbar, submenu=submenu)

        context = self.env.context
 
        doc = etree.XML(res['arch'])

        if view_type in ['form', 'tree']:
            if (not self.env.user.has_group('credit_note_restrict.factura_client_group')) and context.get(
                    'default_move_type') == 'out_invoice':  # Facturas de clientes
                for node_form in doc.xpath("//form"):
                    node_form.set("create", 'false')
                for node_form in doc.xpath("//tree"):
                    node_form.set("create", 'false')

            if (not self.env.user.has_group('credit_note_restrict.credit_note_client_group')) and context.get(
                    'default_move_type') == 'out_refund':  # Notas de credito en clientes
                for node_form in doc.xpath("//form"):
                    node_form.set("create", 'false')
                for node_form in doc.xpath("//tree"):
                    node_form.set("create", 'false')

            if (not self.env.user.has_group('credit_note_restrict.factura_proveedor_group')) and context.get(
                    'default_move_type') == 'in_invoice':  # Facturas en proveedores
                for node_form in doc.xpath("//form"):
                    node_form.set("create", 'false')
                for node_form in doc.xpath("//tree"):
                    node_form.set("create", 'false')

            if (not self.env.user.has_group('credit_note_restrict.reembolso_proveedor_group')) and context.get(
                    'default_move_type') == 'in_refund':  # reembolsos en proveedores
                for node_form in doc.xpath("//form"):
                    node_form.set("create", 'false')
                for node_form in doc.xpath("//tree"):
                    node_form.set("create", 'false')
        res['arch'] = etree.tostring(doc)
        return res


class AccountTranzientReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    
    reason_select = fields.Selection(
        [('devolucion', 'Devolucion'), ('descuento', 'Descuento o Bonificacion'), ('otro', 'Otro')], 'Type',
        default='devolucion')

    def reverse_moves(self):
        _logger.info('REVERSE_MOVES:: en mi funcion')
        if self.reason_select:
            if self.reason_select == 'devolucion':
                self.reason = "Devolucion"
            elif self.reason_select == 'descuento':
                self.reason = 'Descuento o Bonificacion'


        self.ensure_one()
        moves = self.move_ids
        _logger.info("REVERSE_MOVES:: MOVES = %s",moves)
        # Create default values.
        default_values_list = []
        for move in moves:
            default_values_list.append(self._prepare_default_reversal(move))

        batches = [
            [self.env['account.move'], [], True],  # Moves to be cancelled by the reverses.
            [self.env['account.move'], [], False],  # Others.
        ]
        for move, default_vals in zip(moves, default_values_list):
            is_auto_post = bool(default_vals.get('auto_post'))
            is_cancel_needed = not is_auto_post and self.refund_method in ('cancel', 'modify')
            batch_index = 0 if is_cancel_needed else 1
            batches[batch_index][0] |= move
            batches[batch_index][1].append(default_vals)

        # Handle reverse method.
        moves_to_redirect = self.env['account.move']
        for moves, default_values_list, is_cancel_needed in batches:
            new_moves = moves._reverse_moves(default_values_list, cancel=is_cancel_needed)

            if self.refund_method == 'modify':
                moves_vals_list = []
                for move in moves.with_context(include_business_fields=True):
                    moves_vals_list.append(
                        move.copy_data({'date': self.date if self.date_mode == 'custom' else move.date})[0])
                new_moves = self.env['account.move'].create(moves_vals_list)

            moves_to_redirect |= new_moves

        self.new_move_ids = moves_to_redirect
        _logger.info("Movimientos %s",self.new_move_ids)
        for move in self.new_move_ids:
            if self.move_type == 'out_invoice':
                _logger.info("si es out_invoice invoice lines %s ", move.invoice_line_ids)
                for line in move.invoice_line_ids:
                    product_descuento = self.env['product.product'].search(
                        [('is_discount_product', '=', True), ('company_id', '=', move.company_id.id)], limit=1)
                    _logger.info("product desc %s, company %s ", product_descuento,move.company_id.name)
                    if line.product_id.categ_id:
                        if self.reason_select == 'devolucion' and line.product_id.categ_id.account_credit_note_id:
                            line.account_id = line.product_id.categ_id.account_credit_note_id
                        if self.reason_select == 'descuento' and line.product_id.categ_id.account_discount_id:
                            line.account_id = line.product_id.categ_id.account_discount_id
                            if product_descuento :
                                line.product_id = product_descuento.id

        # Create action.
        action = {
            'name': _('Reverse Moves'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
        }
        if len(moves_to_redirect) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': moves_to_redirect.id,
                'context': {'default_move_type': moves_to_redirect.move_type},
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', moves_to_redirect.ids)],
            })
            if len(set(moves_to_redirect.mapped('move_type'))) == 1:
                action['context'] = {'default_move_type': moves_to_redirect.mapped('move_type').pop()}
        return action
