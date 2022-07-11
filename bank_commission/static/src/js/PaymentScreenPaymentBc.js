odoo.define('bank_commission.PaymentScreenPaymentBc', function(require) {
    'use strict';

    const PaymentLineScreen = require('point_of_sale.PaymentScreenPaymentLines');
    const Registries = require('point_of_sale.Registries');

    class PaymentScreenPaymentLines extends PaymentLineScreen {

        selectedLineClass(line) {
//            console.log("Si hereda bien chidoliru");
//            console.log(this);
//            console.log("LINE:: ");
//            console.log(line);
            return { 'payment-terminal': line.get_payment_status() };
        }
        get_is_bank_commission(line){
            console.log("CALCUANDO SI ES COMISION  o NO ..");
            if(line.is_commission === true){
                console.log(" SI ES COMISION DE BANCO");
                return true;
            }
            else{
                return false;
            }

        }

    }
//    PaymentScreenPaymentLines.template = 'PaymentScreenPaymentLinesBc';

    Registries.Component.add(PaymentScreenPaymentLines);

    return PaymentScreenPaymentLines;
});
