odoo.define('pos_customs.PaymentScreenC', function (require) {
"use strict";

var models = require('point_of_sale.models');
const PaymentScreen = require('point_of_sale.PaymentScreen');
const Registries = require('point_of_sale.Registries');
const { isConnectionError } = require('point_of_sale.utils');

var rpc = require('web.rpc');

    const IIPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen{            

            constructor() {
                super(...arguments);
                this.payment_termss;
                this.to_credit_note = false
                this.setInvoiceInfo();
            }

            isCreditNote(){
                return this.to_credit_note
            }

            async clickNotaCredito(){
                console.log("Click en nota de credito")
                console.log(this)
                console.log(this.env.pos.config_id)
                console.log(this.env.pos.get_client())
                console.log(this.currentOrder)
                const config_id = this.env.pos.config_id
                const partner = this.env.pos.get_client()
                
                const partnerInvoices = await this.rpc({
                    model: 'pos.session',
                    method: 'obtener_facturas_anticipo',
                    args: [partner.id, config_id],
                });
                
                
                const selectionInvoiceList = partnerInvoices.map((invoice) => ({
                    id: invoice.id,
                    label: invoice.name + ' $' + invoice.total,
                    item: invoice,
                }));


                const { confirmedInvoice, payload: selectedInvoice } = await this.showPopup('SelectionPopup', {
                    title: this.env._t('Selecciona la factura de anticipo a pagar'),
                    list: selectionInvoiceList,
                });

                if (!selectedInvoice) {
                    return;
                }
                this.selectedCreditNoteId = selectedInvoice
                console.log(this.selectedCreditNoteId)

                this.to_credit_note = !this.to_credit_note;
                this.render();
            }

            async setInvoiceInfo(){
                let vals = await this.rpc({
                            model: 'account.payment.term',
                            method: 'get_all_terms',
                            args: [],
                        });
                this.payment_termss = vals;
                this.render();
            }

            async send_payment(order_id, invoice_data, payments, customer){
                invoice_data['pos_session_id'] = this.currentOrder.pos_session_id

                let mispagos = []
                payments.forEach(element => {
                    var pay = {
                        amount : element.amount,
                        method : element.payment_method
                    } 
                    mispagos.push(pay)
                });

                const createPayment = await this.rpc({
                    model: 'account.payment',
                    method: 'crear_pago_pos',
                    args: [{vals : {invoice : invoice_data, uid : order_id, payments : mispagos, customer : customer}}],
                });

                // console.log(createPayment)
                return createPayment
            }

            async _finalizeValidation() {
                
                console.log("Sobre escribe finalize validation")
                console.log(this.selectedCreditNoteId)

                if ((this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) && this.env.pos.config.iface_cashdrawer) {
                    this.env.pos.proxy.printer.open_cashbox();
                }

                this.currentOrder.initialize_validation_date();
                this.currentOrder.finalized = true;

                let syncedOrderBackendIds = [];

                try {
                    if (this.selectedCreditNoteId){
                        const creditNoteId = null;
                    }
                    else{
                        const creditNoteId = this.selectedCreditNoteId.id;
                    }

                    if (this.currentOrder.is_to_invoice()) {
                        this.currentOrder.to_invoice = [$("#cfdi_usage_sel").val(),$("#payment_termss_selection").val(), creditNoteId];
                        // this.currentOrder.cfdi_usage = $("#cfdi_usage_sel").val();
                        console.log("para facturar ... CURRENT ORDER... ");
                        console.log(this.currentOrder.to_invoice);
                        syncedOrderBackendIds = await this.env.pos.push_and_invoice_order(
                            this.currentOrder
                        );
                    } else {
                        // Isn't original
                        if (this.currentOrder.is_payment_invoice){
                            const myorder = this.currentOrder
                            this.send_payment(myorder.uid, myorder.selected_invoice, myorder.paymentlines.models, myorder.attributes.client)
                        }
                        // console.log("Push single order")
                        syncedOrderBackendIds = await this.env.pos.push_single_order(this.currentOrder);
                    }
                } catch (error) {
                    if (error.code == 700)
                        this.error = true;

                    if ('code' in error) {
                        // We started putting `code` in the rejected object for invoicing error.
                        // We can continue with that convention such that when the error has `code`,
                        // then it is an error when invoicing. Besides, _handlePushOrderError was
                        // introduce to handle invoicing error logic.
                        await this._handlePushOrderError(error);
                    } else {
                        // We don't block for connection error. But we rethrow for any other errors.
                        if (isConnectionError(error)) {
                            this.showPopup('OfflineErrorPopup', {
                                title: this.env._t('Connection Error'),
                                body: this.env._t('Order is not synced. Check your internet connection'),
                            });
                        } else {
                            throw error;
                        }
                    }
                }
                if (syncedOrderBackendIds.length && this.currentOrder.wait_for_push_order()) {
                    const result = await this._postPushOrderResolve(
                        this.currentOrder,
                        syncedOrderBackendIds
                    );
                    if (!result) {
                        await this.showPopup('ErrorPopup', {
                            title: this.env._t('Error: no internet connection.'),
                            body: this.env._t('Some, if not all, post-processing after syncing order failed.'),
                        });
                    }
                }

                this.showScreen(this.nextScreen);

                // If we succeeded in syncing the current order, and
                // there are still other orders that are left unsynced,
                // we ask the user if he is willing to wait and sync them.
                if (syncedOrderBackendIds.length && this.env.pos.db.get_orders().length) {
                    const { confirmed } = await this.showPopup('ConfirmPopup', {
                        title: this.env._t('Remaining unsynced orders'),
                        body: this.env._t(
                            'There are unsynced orders. Do you want to sync these orders?'
                        ),
                    });
                    if (confirmed) {
                        // NOTE: Not yet sure if this should be awaited or not.
                        // If awaited, some operations like changing screen
                        // might not work.
                        this.env.pos.push_orders();
                    }
                }
            }


        };

    Registries.Component.extend(PaymentScreen, IIPaymentScreen);
//    return IIPaymentScreen;

});