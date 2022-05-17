odoo.define('bank_commission.PaymentScreenStatusBc', function (require){
"use strict";

var models = require('point_of_sale.models');
const PaymentScreenStatus = require('point_of_sale.PaymentScreenStatus');
const Registries = require('point_of_sale.Registries');
var rpc = require('web.rpc');

const PaymentScreenStatusBc = (PaymentScreenStatus) =>
    class extends PaymentScreenStatus{
        constructor(){
            super(...arguments);
     /*       console.log("Extiende PaymentscreenStatus BC");
            console.log(this);
            console.log("CURRENT ORDER:: ");
            console.log(this.currentOrder);*/
        }
    };

    /*
    Calcular aquí el total, además agregar una linea más al order por cada método de pago que se usa.
    Si el método de pago se deselecciona, la linea o lineas deben quitarse.

    this.currentOrder.add_product(product, options);  <<-- Agrega otro producto a la orden.

    EJEMPLO: ::
      // Add orderline for each toRefundDetail to the destinationOrder.
            for (const refundDetail of allToRefundDetails) {
                const product = this.env.pos.db.get_product_by_id(refundDetail.orderline.productId);
                const options = this._prepareRefundOrderlineOptions(refundDetail);
                await destinationOrder.add_product(product, options);
                refundDetail.destinationOrderUid = destinationOrder.uid;
            }
    */

    Registries.Component.extend(PaymentScreenStatus, PaymentScreenStatusBc)
});