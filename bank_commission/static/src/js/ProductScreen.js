odoo.define("bank_commission.ProductScreenCustom", function (require) {
    "use strict";

    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    var exports = require("point_of_sale.models");


    const ProductScreenCustom = (ProductScreen) =>
        class extends ProductScreen {
            async _clickProduct(event) {
                console.log("AGREGANDO PRODUCTO .. ");
                if (!this.currentOrder) {
                this.env.pos.add_new_order();
                }
                const product = event.detail;

                const options = await this._getAddProductOptions(product);

                console.log("PRODUCT DETAIL ");
                console.log(product);
                console.log("PRODUCT OPCIONS: ");
                console.log(options);


                // Do not add product if options is undefined.
                if (!options) return;
                // Add the product after having the extra information.
                this.currentOrder.add_product(product, options);
                NumberBuffer.reset();
            }
        }
    Registries.Component.extend(ProductScreen, ProductScreenCustom);
});