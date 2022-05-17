odoo.define('bank_commission.PaymentScreenBc', function (require){
"use strict";

const NumberBuffer = require('point_of_sale.NumberBuffer');
var models = require('point_of_sale.models');
const PaymentScreen = require('point_of_sale.PaymentScreen');
const Registries = require('point_of_sale.Registries');
var rpc = require('web.rpc');
var exports = require("point_of_sale.models");

exports.load_fields('pos.payment.method', ["bank_commission_product_id", "bank_commission_amount", "bank_commission_method"])

const PaymentScreenBc = (PaymentScreen) =>
    class extends PaymentScreen{
        constructor(){
            super(...arguments);
            console.log("Extiende Paymentscreen BC1");
            console.log(this);
        }

        addNewPaymentLine({ detail: paymentMethod }) {

            console.log("COMM METHD");
            console.log(paymentMethod);
            console.log(" ORDER LINES :: ");
            console.log(this.currentOrder.get_orderlines());
            if (paymentMethod.bank_commission_method){

                let product_byid = this.env.pos.db.get_product_by_id(paymentMethod.bank_commission_product_id[0]);
//                console.log("PRODUCTO");
//                console.log(product_byid);

                let price = 0;
                if (paymentMethod.bank_commission_method == "percentage"){
                    let cline = this.currentOrder.get_orderlines().find(line => line.paymentMethod == paymentMethod.id);
                    console.log("LINEA:: ");
                    console.log(cline);
                    price = paymentMethod.bank_commission_amount;
                }
                if (paymentMethod.bank_commission_method == "fixed"){
                    price = paymentMethod.bank_commission_amount;
                }
                this.currentOrder.add_product(product_byid, {
                    quantity: 1,
                    price: price,
                    lst_price: price,
                    extras: {price_manually_set: true,paymentMethod:paymentMethod.id},
                });
                console.log(" YA FUE AGREGADO EL PRODUCTO .. ");
                console.log(this);

            }
            return super.addNewPaymentLine(...arguments);
        }

        deletePaymentLine(event) {
            console.log(" BORRA NDO EL MÉTODO DE PAGO ..   ");
            const { cid } = event.detail;
            const pline = this.paymentLines.find((line) => line.cid === cid);
            console.log(" PLINE .. ");
            console.log(pline);
            super.deletePaymentLine(...arguments);
            let order = this.currentOrder;
            if (pline.payment_method.bank_commission_method){
                let product = pline.payment_method.bank_commission_product_id[0];
                let line = order.get_orderlines().find(line => line.product.id === product && line.paymentMethod === pline.payment_method.id);
                if (line) {
                    order.remove_orderline(line);
                }
            }
        }

        _updateSelectedPaymentline(){
            console.log("Actualizando lineas.. ")
            super._updateSelectedPaymentline(...arguments);
        }
    };

    Registries.Component.extend(PaymentScreen, PaymentScreenBc)
});