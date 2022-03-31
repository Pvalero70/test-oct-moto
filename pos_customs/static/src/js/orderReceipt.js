odoo.define('pos_customs.OrderReceipt', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const OrderReceipt = require('point_of_sale.OrderReceipt');

    const OrderReceipt2 = (OrderReceipt) =>
        class extends OrderReceipt {
        get sale_seller() {
            console.log("Las cosas");
            console.log(this);
            return "HOLASMUNDOS";
        }
    }

    Registries.Component.extend(OrderReceipt, OrderReceipt2);
});
