odoo.define('q_pdv_orders_repair.Orderline', function (require) {
    "use strict";
    
    const models = require('point_of_sale.models');
    var exports = {};
    
    exports.Packlotline = Backbone.Model.extend({
        defaults: {
            lot_name: null
        },
        initialize: function(attributes, options){
            this.order_line = options.order_line;
            if (options.json) {
                this.init_from_JSON(options.json);
                return;
            }
        },
    
        init_from_JSON: function(json) {
            this.order_line = json.order_line;
            this.set_lot_name(json.lot_name);
        },
    
        set_lot_name: function(name){
            this.set({lot_name : _.str.trim(name) || null});
        },
    
        get_lot_name: function(){
            return this.get('lot_name');
        },
    
        export_as_JSON: function(){
            return {
                lot_name: this.get_lot_name(),
            };
        },
    
        add: function(){
            var order_line = this.order_line,
                index = this.collection.indexOf(this);
            var new_lot_model = new exports.Packlotline({}, {'order_line': this.order_line});
            this.collection.add(new_lot_model, {at: index + 1});
            return new_lot_model;
        },
    
        remove: function(){
            this.collection.remove(this);
        }
    });

    models.Orderline = models.Orderline.extend({
        
        setPackLotLinesRepair: function({ modifiedPackLotLines, newPackLotLines }) {
            let lotLinesToRemove = [];

            for (let lotLine of this.pack_lot_lines.models) {
                const modifiedLotName = modifiedPackLotLines[lotLine.cid];
                if (modifiedLotName) {
                    lotLine.set({ lot_name: modifiedLotName });
                } else {
                    lotLinesToRemove.push(lotLine);
                }
            }

            for (let lotLine of lotLinesToRemove) {
                lotLine.remove();
            }
    
            let newPackLotLine;
            for (let newLotLine of newPackLotLines) {
                newPackLotLine = new exports.Packlotline({}, { order_line: this });
                newPackLotLine.set({ lot_name: newLotLine});
                this.pack_lot_lines.add(newPackLotLine);
            }
            this.pack_lot_lines.set_quantity_by_lot();
        },
    });
    
});