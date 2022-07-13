odoo.define('bank_commission.PaymentScreenPaymentBc', function(require) {
    'use strict';

    const PaymentLineScreen = require('point_of_sale.PaymentScreenPaymentLines');
    const Registries = require('point_of_sale.Registries');

    class PaymentScreenPaymentLines extends PaymentLineScreen {
        get_is_bank_commission(line){
            if(line.is_commission === true){
                return true;
            }
            else{
                return false;
            }
        }
    }
    Registries.Component.add(PaymentScreenPaymentLines);

    return PaymentScreenPaymentLines;
});
