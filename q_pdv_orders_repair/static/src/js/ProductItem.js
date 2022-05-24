odoo.define('q_pdv_orders_repair.ProductItem', function(require) {
    'use strict';
    
    const Registries = require('point_of_sale.Registries');
    var ProductItem = require('point_of_sale.ProductItem');

    const ProductItemInherit = ProductItem => class extends ProductItem {
        add_product_cart(product) {
            this.env.pos.get_order().add_product(product, {
                merge: false
            })
        }
    };
    Registries.Component.extend(ProductItem, ProductItemInherit);
    return ProductItem;
});