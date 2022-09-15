odoo.define('pos_customs.PaymentScreenC', function (require) {
"use strict";

const { useState } = owl.hooks;
var models = require('point_of_sale.models');
const PaymentScreen = require('point_of_sale.PaymentScreen');
const Registries = require('point_of_sale.Registries');
var exports = require("point_of_sale.models");
const { isConnectionError } = require('point_of_sale.utils');

var rpc = require('web.rpc');

exports.load_fields('pos.payment', ["is_commission"])

    const IIPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen{            

            constructor() {
                super(...arguments);
                this.payment_termss;
                this.sale_terms;
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

                if(!partner){
                    return;
                }
                
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

                const paylaterPaymentMethod = this.env.pos.payment_methods.filter(
                    (method) =>
                        this.env.pos.config.payment_method_ids.includes(method.id) && method.type == 'pay_later'
                )[0];

                const paylaterPayment = this.currentOrder.add_paymentline(paylaterPaymentMethod);
                console.log(selectedInvoice.total)
                paylaterPayment.set_amount(selectedInvoice.total);
            }

            async setInvoiceInfo(){
                var vals = await this.rpc({
                            model: 'account.payment.term',
                            method: 'get_all_terms',
                            args: [],
                        });


                console.log("## current order ##");

                var selectedOrderline = this.currentOrder.get_selected_orderline();
                if(selectedOrderline && selectedOrderline.sale_order_origin_id){
                    let sale_order = await this.rpc({
                            model: 'sale.order',
                            method: 'get_sale_order',
                            args: [{'id':selectedOrderline.sale_order_origin_id.id}],
                        });
                    this.sale_terms = sale_order;
                    if(Array.isArray(sale_order)){
                        for (let value of vals) {
                          if(value[0] == sale_order[0]){
                            value[2] = true;
                          }
                        }
                    }

                }

                this.payment_termss = vals;
                this.render();



            }
            async create_commission_invoice(order){
                let invoice_data = {
                    model: 'pos.order',
                    method: 'create_comm_inv_pos',
                    args: [order.name],
                };
                const comm_invoice = await this.rpc(invoice_data);
                return comm_invoice;
            }

            async send_payment(order, invoice_data, payments, customer){

                invoice_data['pos_session_id'] = this.currentOrder.pos_session_id
                invoice_data['order_id'] = this.currentOrder.id

                console.log(" EL POS ORDER :: ");
                console.log(order);
                let mispagos = []
                payments.forEach(element => {
                    var pay = {
                        amount : element.amount,
                        method : element.payment_method
                    } 
                    mispagos.push(pay)
                });
                let pos_order_lines = []
                order.orderlines.models.forEach(el=>{
                    var line = {
                        amount: el.price,
                        product_id: el.product.id
                    }
                    pos_order_lines.push(line);
                });
                console.log("Order lines ... ");
                console.log(pos_order_lines);
                let createpayment_data = {
                    model: 'account.payment',
                    method: 'crear_pago_pos',
                    args: [{vals : {
                            invoice : invoice_data,
                            uid : order.uid,
                            order_lines_data: pos_order_lines,
                            payments : mispagos,
                            customer : customer
                        }}],
                };
                const createPayment = await this.rpc(createpayment_data);
                // console.log(createPayment)
                return createPayment
            }

            async _finalizeValidation() {
                
                console.log("Sobre escribe finalize validation")
                console.log(this.selectedCreditNoteId)

                console.log("Is paid with cash")
                console.log(this.currentOrder.is_paid_with_cash())

                console.log("Config")
                console.log(this.env.pos.config)

                let monto_efectivo_max = this.env.pos.config.monto_efectivo_max || 0;
                let monto_pago_max = this.env.pos.config.monto_pago_max || 0;

                console.log("Payment Lines")
                // console.log(this.currentOrder.paymentlines.models)

                let payments = this.currentOrder.paymentlines.models
                let monto_efectivo = 0;
                let monto_total = 0;

                let partner = this.currentOrder.attributes.client
                console.log("Cliente")
                console.log(partner)
                

                const saldo_pagado = await this.rpc({
                    model: 'account.move',
                    method: 'validar_saldo_permitido',
                    args: [{vals : {partner : partner}}],
                });

                console.log("Saldo pagado ultimos 6 meses")
                console.log(saldo_pagado)

                for (let i = 0; i < payments.length; i++) {
                    
                    if (payments[i]['name'].toLowerCase().search('efectivo') >= 0){
                        console.log("Efectivo")
                        console.log(payments[i])
                        monto_efectivo += payments[i].amount;
                    }
                    else{
                        console.log("Otros")
                        console.log(payments[i])
                    }
                    monto_total += payments[i].amount
                }

                let emails = this.env.pos.config.email_notificacion_sat
                let sucursal = this.env.pos.config.name
                let cliente = partner.name
                let monto = 0
                let venta = this.currentOrder.name

                if (monto_efectivo > monto_efectivo_max){

                        const { confirmed } = await this.showPopup('ConfirmPopup', {
                            title: "Valida Pago",
                            body: "Reportar al SAT que el cliente ha rebasado el límite permitido de pago en efectivo."
                        });
                        if(confirmed){

                            console.log("Confirmacion")
                            console.log(confirmed);      
                            monto = monto_efectivo

                            console.log(emails)
                            console.log(sucursal)
                            console.log(cliente)
                            console.log(monto)
                            console.log(venta)

                            await this.rpc({
                                model: 'account.move',
                                method: 'enviar_mail_advertencia_pago_permitido',
                                args: [{vals : {emails : emails, sucursal : sucursal, cliente: cliente, monto: monto, venta: venta}}],
                            });
                        }
                }

                let monto_pagado_total = parseFloat(monto_total) + parseFloat(saldo_pagado)
                
                if (monto_pagado_total > monto_pago_max){

                    const { confirmed } = await this.showPopup('ConfirmPopup', {
                        title: "Valida Pago",
                        body: "Reportar al SAT que el cliente ha rebasado el límite permitido de compra."
                    });
                    if(confirmed){
                        console.log("Confirmacion")
                        console.log(confirmed);  
                        
                        monto = monto_pagado_total
                        
                        console.log(emails)
                        console.log(sucursal)
                        console.log(cliente)
                        console.log(monto)
                        console.log(venta)

                        await this.rpc({
                            model: 'account.move',
                            method: 'enviar_mail_advertencia_pago_permitido',
                            args: [{vals : {emails : emails, sucursal : sucursal, cliente: cliente, monto: monto, venta: venta}}],
                        });

                    }
                }

                if ((this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) && this.env.pos.config.iface_cashdrawer) {
                    this.env.pos.proxy.printer.open_cashbox();
                }

                console.log("Continua...")

                this.currentOrder.initialize_validation_date();
                this.currentOrder.finalized = true;

                let syncedOrderBackendIds = [];

                try {

                    
                    if (this.currentOrder.is_to_invoice()) {
                        if (this.selectedCreditNoteId){
                            this.currentOrder.to_invoice = [$("#cfdi_usage_sel").val(), $("#payment_termss_selection").val(), this.selectedCreditNoteId.id];                            
                        }
                        else{
                            this.currentOrder.to_invoice = [$("#cfdi_usage_sel").val(), $("#payment_termss_selection").val(), null];
                        }
                        console.log("para facturar ... CURRENT ORDER... ");
                        console.log(this.currentOrder.to_invoice);
                        syncedOrderBackendIds = await this.env.pos.push_and_invoice_order(
                            this.currentOrder
                        );
                    } else {
                        // Isn't original
                        if (this.currentOrder.is_payment_invoice){
                            const myorder = this.currentOrder
                            this.send_payment(myorder, myorder.selected_invoice, myorder.paymentlines.models, myorder.attributes.client)
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
                this.create_commission_invoice(this.currentOrder);
            }


        };

    Registries.Component.extend(PaymentScreen, IIPaymentScreen);
//    return IIPaymentScreen;

});