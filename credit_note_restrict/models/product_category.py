# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, Warning
# import xml.etree.ElementTree as etree
from lxml import etree

_logger = logging.getLogger(__name__)


class ResUserInheritDiscount(models.Model):
    _inherit = 'product.template'

    is_discount_product = fields.Boolean("Es producto descuento", default=False)


class ResUserInheritDiscount(models.Model):
    _inherit = 'product.category'

    account_credit_note_id = fields.Many2one('account.account', "Cuenta de devolucion")
    account_discount_id = fields.Many2one('account.account', "Cuenta de descuento o bonificacion")


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def write(self, vals):
        _logger.info("Vals en account line %s", vals)
        return super(AccountMoveLine, self).write(vals)


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        _logger.info("Vals en account move %s", vals)
        return super(AccountMoveInherit, self).write(vals)

    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids(self):
        _logger.info("ACCOUNT MOVE: Ejecutar funcion privada")
        res = super(AccountMoveInherit, self)._onchange_invoice_line_ids()
        _logger.info("ACCOUNT MOVE: Despues de ejecutar funcion con res %s", res)
        return res

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

        _logger.info("REVERSE_MOVES:: MOVES = %s", moves)
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
            _logger.info("valores default move %s, y moves = %s", default_values_list, moves)
            new_moves = moves._reverse_moves(default_values_list, cancel=is_cancel_needed)

            if self.refund_method == 'modify':
                moves_vals_list = []
                for move in moves.with_context(include_business_fields=True):
                    moves_vals_list.append(
                        move.copy_data({'date': self.date if self.date_mode == 'custom' else move.date})[0])
                _logger.info("valores move %s", moves_vals_list)
                new_moves = self.env['account.move'].create(moves_vals_list)
            _logger.info("New moves = %s", new_moves)
            moves_to_redirect |= new_moves

        self.new_move_ids = moves_to_redirect
        total = 0
        _logger.info("Movimientos %s", self.new_move_ids)

        if self.move_type == 'out_invoice':
            product_descuento = self.env['product.product'].search(
                [('is_discount_product', '=', True), ('company_id', '=', move.company_id.id)], limit=1)

            if self.reason_select == 'descuento':
                total_sum = sum([(line.quantity * line.price_unit) for move in self.new_move_ids for line in move.invoice_line_ids])
                ids_lines = [(2,line.id) for move in self.new_move_ids for line in move.invoice_line_ids]
                ids_lines.pop(0)
                for move in self.new_move_ids:
                    num_line = 1
                    for line in move.invoice_line_ids:

                        if num_line == 1:
                            num_line += 1
                            line.account_id = line.product_id.categ_id.account_discount_id
                            line.product_id = product_descuento

                            ids_lines.append((1,line.id,{'product_id':product_descuento.id,'quantity': 1, 'price_unit': total_sum, 'amount_currency': line.amount_currency}))

                            _logger.info("Hacemos write %s" ,{'invoice_line_ids':ids_lines} )
                            move.write({'invoice_line_ids':ids_lines})
                            _logger.info("Terminamos de hacer write")
                            _logger.info("Calculamos total")
                            line._onchange_price_subtotal()
                            continue


            for move in self.new_move_ids:
                _logger.info("si es out_invoice invoice lines %s ", move.invoice_line_ids)
                for line in move.invoice_line_ids:

                    _logger.info("product desc %s, company %s ", product_descuento, move.company_id.name)
                    if line.product_id.categ_id:
                        if self.reason_select == 'devolucion' and line.product_id.categ_id.account_credit_note_id:
                            line.account_id = line.product_id.categ_id.account_credit_note_id
                            line._onchange_account_id()
                        if self.reason_select == 'descuento' and line.product_id.categ_id.account_discount_id:
                            line.account_id = line.product_id.categ_id.account_discount_id
                            if not product_descuento:
                                raise ValidationError(_("No se ha definido un producto para Descuentos "))
                            _logger.info("Modificamos")



                            _logger.info("Cant %s , precio %s, total %s", 1, total_sum, total)
                            line.product_id = product_descuento

                            line._onchange_account_id()
                            _logger.info("Cambiamos producto")
                            line._onchange_product_id()

                            line.write({'quantity': 1, 'price_unit': total, 'amount_currency': line.amount_currency})
                            _logger.info("en price subtottal")
                            _logger.info("Calculamos total")
                            line._onchange_price_subtotal()
                _logger.info("guardamos nota credito")
                move._onchange_invoice_line_ids()

        # line._onchange_price_subtotal()

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
