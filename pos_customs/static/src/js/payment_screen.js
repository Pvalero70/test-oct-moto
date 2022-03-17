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
            }
            async setInvoiceInfo(){
                console.log("____Lanzando popup de Metodo de pago");
                await this.showPopup('SetInvoiceInfoPopupWidget');
            }


        };

    Registries.Component.extend(PaymentScreen, IIPaymentScreen);
    return IIPaymentScreen;

});