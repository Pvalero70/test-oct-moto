odoo.define('q_pdv_orders_repair.models', function(require) {

    'use strict';

    var models = require('point_of_sale.models');
    var super_order_line_model = models.Order.prototype;

    models.Order = models.Order.extend({
        initialize: function(attr, options) {
            super_order_line_model.initialize.call(this, attr, options);
            this.ref_repair = this.ref_repair || this.ref_repair;
        },
        init_from_JSON: function (json) {
            super_order_line_model.init_from_JSON.apply(this, arguments);
            this.ref_repair = json.ref_repair ? json.ref_repair : false;
        },
        export_as_JSON: function () {
            const json = super_order_line_model.export_as_JSON.apply(this, arguments);
            json.ref_repair = this.ref_repair;
            return json;
        },
        set_repair: function(ref_repair) {
            this.ref_repair = ref_repair;
        },
    });

});