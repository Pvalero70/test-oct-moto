odoo.define('pos_custom_settle_due.PaymentScreen', function (require) {
    'use strict';

    const PaymentScreen = require('pos_settle_due.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const { float_is_zero } = require('web.utils');
    const { patch } = require('web.utils');

    patch(PaymentScreen.prototype, "prototype patch", {
        async validateOrder() {
            console.log('###Sobre escribe nuevo###')
        }
    });

    // const PosSettleDuePaymentScreenCustom = (PaymentScreen) =>
    //     class extends PaymentScreen {
    //         async validateOrder() {
    //             console.log('###Sobre escribe###')
    //         };
    //     };

    // Registries.Component.extend(PaymentScreen, PosSettleDuePaymentScreenCustom);

    // return PaymentScreen;
});