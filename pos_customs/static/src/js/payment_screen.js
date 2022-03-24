odoo.define('pos_customs.PaymentScreenC', function (require) {
"use strict";
console.log("Carga el chow");

var models = require('point_of_sale.models');
const PaymentScreen = require('point_of_sale.PaymentScreen');
const Registries = require('point_of_sale.Registries');
var rpc = require('web.rpc');

    const IIPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen{
            constructor() {
                super(...arguments);
                this.variable_prueba = this.setInvoiceInfo();
            }

            async setInvoiceInfo(){
                console.log("____Lanzando popup de Metodo de pago");
                return [1,2,3,4,56]
            }


            async _finalizeValidation() {
            if ((this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) && this.env.pos.config.iface_cashdrawer) {
                this.env.pos.proxy.printer.open_cashbox();
            }

            this.currentOrder.initialize_validation_date();
            this.currentOrder.finalized = true;

            let syncedOrderBackendIds = [];

            try {
                if (this.currentOrder.is_to_invoice()) {
                    console.log(" Current order :: ");
                    console.log(this.currentOrder);
                   this.currentOrder.to_invoice = [$("#cfdi_usage_sel").val()];
                    // this.currentOrder.cfdi_usage = $("#cfdi_usage_sel").val();

                    syncedOrderBackendIds = await this.env.pos.push_and_invoice_order(
                        this.currentOrder
                    );
                } else {
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