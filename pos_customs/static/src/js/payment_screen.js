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
            setPaymentMethod(){
                console.log("____Lanzando popup de Metodo de pago");
            }
            setCfdiUsage(){
                console.log("____Lanzando popup de uso de CFDI");
            }

        };

    Registries.Component.extend(PaymentScreen, IIPaymentScreen);
    return IIPaymentScreen;

});