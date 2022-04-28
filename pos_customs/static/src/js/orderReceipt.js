odoo.define('pos_customs.OrderReceipt', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const OrderReceipt = require('point_of_sale.OrderReceipt');

    const OrderReceipt2 = (OrderReceipt) =>
        class extends OrderReceipt {
        get sale_seller() {
//            Get the first line to get user of sale.order object.
            console.log("THIS ==>> ");
            console.log(this);
            console.log(" ORDER LINES :: == >>> ");
            console.log(this.orderlines)
            var order_liness = this.orderlines[0];
            console.log(order_liness);
            if(order_liness["sale_order_origin_id"] == undefined){
                console.log("SALE ORDER ORI NO FOUND");
                return "--";
            }
            var sale_order = order_liness.sale_order_origin_id;
            console.log(sale_order);
            if(sale_order["user_id"] != undefined){
                console.log("definido");
                var seller_name = this.orderlines[0].sale_order_origin_id.user_id[1];
                return seller_name;
            }
            else{
                console.log("indefinido");
            }
            return "Holsss";
//            so_user = sale_order.sale_order_origin_id.user_id;
            /*if(so_user == undefined){
                return "-";
            }
            else{

            }*/
        }
    }

    Registries.Component.extend(OrderReceipt, OrderReceipt2);
});
