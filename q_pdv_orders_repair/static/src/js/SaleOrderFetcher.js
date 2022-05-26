odoo.define('q_pdv_orders_repair.SaleOrderFetcher', function (require) {
    "use strict";

    const { patch } = require('web.utils');
    const SaleOrderFetcher = require('pos_sale.SaleOrderFetcher');

    patch(SaleOrderFetcher, "static patch", {

        async _getOrderIdsForCurrentPage(limit, offset) {
            return await this.rpc({
                model: 'sale.order',
                method: 'search_read',
                args: [[], ['name', 'partner_id', 'amount_total', 'date_order', 'state', 'user_id'], offset, limit],
                context: this.comp.env.session.user_context,
            });
        },

        async _getRepairsIdsForCurrentPage(limit, offset) {
            let res = await this.rpc({
                model: 'stock.picking.type',
                method: 'search_read',
                args: [[['id', '=', this.comp.env.pos.config.picking_type_id[0]]], ['default_location_src_id'], offset, limit],
            });
            let location_src = res[0]['default_location_src_id'][0]
            return await this.rpc({
                model: 'repair.order',
                method: 'search_read',
                args: [[['state', '=', '2binvoiced'],['location_id', '=', location_src]], ['name', 'partner_id', 'amount_total', 'schedule_date', 'state', 'user_id'], offset, limit],
            });
        },

        async _fetch(limit, offset) {
            const sale_orders = await this._getOrderIdsForCurrentPage(limit, offset);
            sale_orders.map(element => {
                element.model = 'sale';
            })
            const sale_repairs = await this._getRepairsIdsForCurrentPage(limit, offset);
            sale_repairs.map(element => {
                element.date_order = element.schedule_date;
                element.model = 'repair';      
                delete element.schedule_date;
                return element;
            })
            var sale_orders_real = sale_orders.concat(sale_repairs)
            this.totalCount = sale_orders_real.length;
            return sale_orders_real;
        }

    });
});