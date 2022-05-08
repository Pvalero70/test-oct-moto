odoo.define('pos_custom_settle_due.PaymentScreen', function (require) {
    'use strict';

    const PaymentScreen = require('pos_settle_due.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const { float_is_zero } = require('web.utils');
    const { patch } = require('web.utils');

    patch(PaymentScreen, "static patch", { 

        async validateOrder() {

            console.log("### VALIDA ###")
            return
        }

    });

});