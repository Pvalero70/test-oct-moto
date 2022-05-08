odoo.define('pos_custom_settle_due.ClientLine', function (require) {
    'use strict';

    const ClientLine = require('point_of_sale.ClientLine');
    const Registries = require('point_of_sale.Registries');

    const POSSettleDueClientLineCustom = (ClientLine) =>
        class extends ClientLine {
            getPartnerLink() {
                return `/web#model=res.partner&id=${this.props.partner.id}`;
            }
            async settleCustomerInvoiceDue(event) {
                if (this.props.selectedClient == this.props.partner) {
                    event.stopPropagation();
                }
                console.log("Da clic")
                console.log(this.props.partner.id)
                console.log(this.env.pos.db.partner_sorted)

                const partnerInvoices = await this.rpc({
                    model: 'account.move',
                    method: 'search_read',
                    args: [[['partner_id', '=', this.props.partner.id]], ['name', 'amount_total', 'amount_residual_signed', 'state']],
                    // args: [[['partner_id', '=', this.props.partner.id], ['payment_state', '=', 'not_paid'], ['state', '=', 'posted']], ['name', 'amount_total', 'amount_residual_signed', 'state']],
                });
                
                console.log(partnerInvoices)

                // const totalDue = this.props.partner.total_due;
                // const paymentMethods = this.env.pos.payment_methods.filter(
                //     (method) => this.env.pos.config.payment_method_ids.includes(method.id) && method.type != 'pay_later'
                // );
                const selectionInvoiceList = partnerInvoices.map((invoice) => ({
                    id: invoice.id,
                    label: invoice.name + ' $' + invoice.amount_residual_signed,
                    item: invoice,
                }));


                const { confirmed, payload: selectedInvoice } = await this.showPopup('SelectionPopup', {
                    title: this.env._t('Selecciona la factura a pagar'),
                    list: selectionInvoiceList,
                });

                console.log("Factura seleccionada")
                console.log(selectedInvoice)
                if (!confirmed) return;

                const paymentMethods = this.env.pos.payment_methods.filter(
                    (method) => this.env.pos.config.payment_method_ids.includes(method.id) && method.type != 'pay_later'
                );
                const selectionList = paymentMethods.map((paymentMethod) => ({
                    id: paymentMethod.id,
                    label: paymentMethod.name,
                    item: paymentMethod,
                }));
                
                const { confirmed, payload: selectedPaymentMethod } = await this.showPopup('SelectionPopup', {
                    title: this.env._t('Selecciona el metodo de pago para la factura'),
                    list: selectionList,
                });
                if (!confirmed) return;

                this.trigger('discard'); // make sure the ClientListScreen resolves and properly closed.
                const newOrder = this.env.pos.add_new_order();
                const payment = newOrder.add_paymentline(selectedPaymentMethod);
                payment.set_amount(selectedInvoice.amount_residual_signed);
                newOrder.set_client(this.props.partner);
                this.showScreen('PaymentScreen');
            }
        };

    Registries.Component.extend(ClientLine, POSSettleDueClientLineCustom);

    return ClientLine;
});