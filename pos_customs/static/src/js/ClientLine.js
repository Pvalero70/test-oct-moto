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
                console.log("2");
                if (this.props.selectedClient == this.props.partner) {
                    event.stopPropagation();
                }
                // console.log("Da clic")
                // console.log(this)
                // console.log(this.env.pos.config.name)
                // console.log(this.env.pos.company.id)
                // console.log(this.props.partner.id)
                // console.log(this.env.pos.db.partner_sorted)

                const company_id = this.env.pos.company.id
                const config_name = this.env.pos.config.name

                const partnerInvoices = await this.rpc({
                    model: 'account.move',
                    method: 'search_read',
                    // args: [[['partner_id', '=', this.props.partner.id]], ['name', 'amount_total', 'amount_residual_signed', 'state']],
                    args: [[['company_id', '=', company_id], ['partner_id', '=', this.props.partner.id], ['ref', 'ilike', config_name], ['state', '=', 'posted'], ['amount_residual_signed', '>', 0]], ['name', 'amount_total', 'amount_residual_signed', 'state']],
                });
                
                // console.log(partnerInvoices)

                // const totalDue = this.props.partner.total_due;
                // const paymentMethods = this.env.pos.payment_methods.filter(
                //     (method) => this.env.pos.config.payment_method_ids.includes(method.id) && method.type != 'pay_later'
                // );
                const selectionInvoiceList = partnerInvoices.map((invoice) => ({
                    id: invoice.id,
                    label: invoice.name + ' $' + invoice.amount_residual_signed,
                    item: invoice,
                }));


                const { confirmedInvoice, payload: selectedInvoice } = await this.showPopup('SelectionPopup', {
                    title: this.env._t('Selecciona la factura a pagar'),
                    list: selectionInvoiceList,
                });
                
                // console.log("Factura seleccionada")
                // console.log(selectedInvoice)
                // console.log(confirmedInvoice)

                if (!selectedInvoice) return;

                const paymentMethods = this.env.pos.payment_methods.filter(
                    (method) => this.env.pos.config.payment_method_ids.includes(method.id) && method.type != 'pay_later'
                );
                // console.log(paymentMethods)
                const selectionList = paymentMethods.map((paymentMethod) => ({
                    id: paymentMethod.id,
                    label: paymentMethod.name,
                    item: paymentMethod,
                }));
                // console.log(selectionList)
                const { confirmed, payload: selectedPaymentMethod } = await this.showPopup('SelectionPopup', {
                    title: this.env._t('Selecciona el metodo de pago para la factura'),
                    list: selectionList,
                });
                // console.log(confirmed)
                if (!confirmed) return;
                // console.log("Pasa")

                // Aquí revisamos si se debe o no aplicar la comisión del banco
                if (selectedPaymentMethod.bank_commission_method){
                    // Seleccionamos el método de pago de la comisión
                    const { confirmed2, payload: selectedCommissionPaymentMethod } = await this.showPopup('SelectionPopup', {
                        title: this.env._t('Selecciona el metodo de pago de comisión'),
                        list: selectionList,
                    });
                    console.log("1 CONFIRMED 2 :: "+confirmed2);
                    // if (!confirmed2) return;
                    this.trigger('discard'); // make sure the ClientListScreen resolves and properly closed.

                    const newOrder = this.env.pos.add_new_order();

                    console.log("This")
                    console.log(this)
                    console.log("payment method Commission: ");
                    console.log(selectedCommissionPaymentMethod)
                    // Calculamos el monto de la comisión
                    let  commprice = 0;
                    if(selectedPaymentMethod.bank_commission_method == "percentage"){
                        // Calculo de la comisión en base al monto a pagar.
                        // CALCULAAAAAARRRR AQUI
                        // validar cuales son las lineas que van a generar una comision deacuerdo a la categ del producto.
                        commprice = 1000;
                    }
                    if (selectedPaymentMethod.bank_commission_method == "fixed"){
                        commprice = selectedPaymentMethod.bank_commission_amount;
                    }
                    // Creamos una nueva orden para pagar únicamente la comisión.
                    if(commprice > 0){
                        console.log("1");
                        let product_id = selectedPaymentMethod.bank_commission_product_id[0];
                        let product_byid = this.env.pos.db.get_product_by_id(product_id);
                        // this.trigger('discard');
                        // let newCommOrder = this.env.pos.add_new_order();
                        newOrder.add_product(product_byid, {
                            quantity: 1,
                            price: commprice,
                            lst_price: commprice,
                            extras: {price_manually_set: true,paymentMethod:selectedCommissionPaymentMethod.id},
                        });
                        const payment_com = newOrder.add_paymentline(selectedCommissionPaymentMethod);
                        payment_com.set_amount(commprice);
                    }

                    const payment = newOrder.add_paymentline(selectedPaymentMethod);
                    payment.set_amount(selectedInvoice.amount_residual_signed);
                    newOrder.set_client(this.props.partner);
                    newOrder.is_payment_invoice = true;
                    newOrder.selected_invoice = selectedInvoice;
                    this.showScreen('PaymentScreen');
                }


            }
        };

    Registries.Component.extend(ClientLine, POSSettleDueClientLineCustom);

    return ClientLine;
});