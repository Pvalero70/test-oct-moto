odoo.define('bank_commission.PaymentScreenBc', function (require){
"use strict";

const NumberBuffer = require('point_of_sale.NumberBuffer');
var models = require('point_of_sale.models');
const PaymentScreen = require('point_of_sale.PaymentScreen');
const Registries = require('point_of_sale.Registries');
var rpc = require('web.rpc');
var exports = require("point_of_sale.models");

exports.load_fields('pos.payment.method', ["bank_commission_product_id", "bank_commission_amount", "bank_commission_method", "product_cate_commission_ids"])

const PaymentScreenBc = (PaymentScreen) =>
    class extends PaymentScreen{
        constructor(){
            super(...arguments);
        }

        addNewPaymentLine({ detail: paymentMethod }) {
            if (paymentMethod.bank_commission_method){

                // Decide if add commission or not.
                /* Solo debe afectar a los productos motos de Vehículos TT y en las demás compañias debe afectar al resto si afecta a otros productos. */
                /*
                console.log("MÉTodo de pago :: ");
                console.log(paymentMethod);
                console.log("LINEAS DEL POS ORDER ACTUAL:: ");
                console.log(this.currentOrder.get_orderlines());
                */
                let product_categ_id_list = [];
                // let product_categ_parents_id_list = [];
                this.currentOrder.get_orderlines().forEach(element => {
                    if(product_categ_id_list.includes(element.product.categ.id) == false){
                        product_categ_id_list.push(element.product.categ.id);
                    }
                    if(product_categ_id_list.includes(element.product.categ.parent_id[0]) == false){
                        product_categ_id_list.push(element.product.categ.parent_id[0]);
                    }

                });
//                console.log("Lista de ids de categorias de produtos y sus padres. ");
//                console.log(product_categ_id_list);
                let intersection = paymentMethod.product_cate_commission_ids.filter(element => product_categ_id_list.includes(element));
                console.log("Coincidencias de categorias de prod:: ");
                console.log(intersection);
                if(intersection.length >= 1){
                    let product_id = paymentMethod.bank_commission_product_id[0];
                    let product_byid = this.env.pos.db.get_product_by_id(product_id);
                    let oline = this.currentOrder.get_orderlines().find(line => line.product.id === product_id);
                    let current_com = 0;
                    if (oline && this.currentOrder.get_due() > 0){
                        current_com = oline.price;
                    }
                    let price = 0;
                    if (paymentMethod.bank_commission_method == "percentage"){
                        let total_due = this.currentOrder.get_total_with_tax()-current_com-this.currentOrder.get_total_paid()+ this.currentOrder.get_rounding_applied();
                        price = total_due * (paymentMethod.bank_commission_amount/100);
                        //price = this.currentOrder.get_due() * (paymentMethod.bank_commission_amount/100);
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
                }

            }
            return super.addNewPaymentLine(...arguments);
        }

        deletePaymentLine(event) {
            const { cid } = event.detail;
            const pline = this.paymentLines.find((line) => line.cid === cid);
            super.deletePaymentLine(...arguments);
            let order = this.currentOrder;
            // TODO: Al quitar una es necesario reecalcular las demás para volver agregar la comisión.
            if (pline.payment_method.bank_commission_method){
                let product = pline.payment_method.bank_commission_product_id[0];
                let line = order.get_orderlines().find(line => line.product.id === product && line.paymentMethod === pline.payment_method.id);
                if (line) {
                    order.remove_orderline(line);
                }
            }
        }

        _updateSelectedPaymentline(){
            super._updateSelectedPaymentline(...arguments);
            let pline = this.selectedPaymentLine;
            let order = this.currentOrder;
            let oline = order.get_orderlines().find(line => line.paymentMethod === pline.payment_method.id && line.product.id === pline.payment_method.bank_commission_product_id[0]);
            if (oline) {
                let com_total = pline.amount * (pline.payment_method.bank_commission_amount/100);
                oline.set_unit_price(com_total);
                // Obtenemos el total de la compra y le restamos la comisión actual.
                // reecalculamos la comisión
            }
        }
    };

    Registries.Component.extend(PaymentScreen, PaymentScreenBc)
});