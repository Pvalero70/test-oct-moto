odoo.define('pos_customs.OrderReceipt', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const OrderReceipt = require('point_of_sale.OrderReceipt');

    const OrderReceipt2 = (OrderReceipt) =>
        class extends OrderReceipt {
            get sale_seller() {
    //            Get the first line to get user of sale.order object.
                if (this.orderlines){
                    console.log("Orderlines")
                    console.log(this.orderlines)
                    var order_liness = this.orderlines[0];
                    console.log("Orderlines2")
                    console.log(order_liness)
                    if(order_liness["sale_order_origin_id"] == undefined){
                        return false;
                    }
                    var sale_order = order_liness.sale_order_origin_id;
                    if(sale_order["user_id"] != undefined){
                        var seller_name = this.orderlines[0].sale_order_origin_id.user_id[1];
                        return seller_name;
                    }
                    else{
                        return false;
                    }
                }
            }
    }

    Registries.Component.extend(OrderReceipt, OrderReceipt2);
});
