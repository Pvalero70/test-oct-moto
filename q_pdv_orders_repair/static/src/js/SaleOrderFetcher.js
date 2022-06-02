odoo.define('q_pdv_orders_repair.SaleOrderFetcher', function (require) {
    "use strict";

    const { patch } = require('web.utils');
    const SaleOrderFetcher = require('pos_sale.SaleOrderFetcher');

    patch(SaleOrderFetcher, "static patch", {

        async _getOrderIdsForCurrentPage(limit, offset) {
            console.log("## Get orders current page ##")
            if (this.searchDomain == undefined){

                if (this.comp.env.pos.config.crm_team_id){
                    let team_id = this.comp.env.pos.config.crm_team_id;
                    this.searchDomain = [
                        ['team_id', '=', team_id[0]],
                        ['state', 'in', ['sale']],
                        ['invoice_status', 'in', ['to invoice']]
                    ]
                }
                else{
                    this.searchDomain = [
                        ['state', 'in', ['sale']]
                        ['invoice_status', 'in', ['to invoice']]
                    ]
                }
            }
            else{
                this.searchDomain[0] = ['state', 'in', ['sale']]
                this.searchDomain[1] = ['invoice_status', 'in', ['to invoice']]

                if (this.comp.env.pos.config.crm_team_id){
                    let team_id = this.comp.env.pos.config.crm_team_id;
                    this.searchDomain.unshift(['team_id', '=', team_id[0]]);
                }
            }
            
            console.log(this.searchDomain)

            return await this.rpc({
                model: 'sale.order',
                method: 'search_read',
                args: [this.searchDomain ? this.searchDomain : [], ['name', 'partner_id', 'amount_total', 'date_order', 'state', 'user_id', 'team_id'], offset, limit],
                context: this.comp.env.session.user_context,
            });
        },

        async _getRepairsIdsForCurrentPage(limit, offset) {
            
            console.log("## Get repair orders ##")

            let res = await this.rpc({
                model: 'stock.picking.type',
                method: 'search_read',
                args: [[['id', '=', this.comp.env.pos.config.picking_type_id[0]]], ['default_location_src_id'], offset, limit],
            });

            console.log(res)
            
            console.log(" ## Location ##")
            let location_src = res[0]['default_location_src_id'][0]
            console.log(location_src)
            
            return await this.rpc({
                model: 'repair.order',
                method: 'search_read',
                args: [[['state', '=', '2binvoiced'],['location_id', '=', location_src]], ['name', 'partner_id', 'amount_total', 'schedule_date', 'state', 'user_id'], offset, limit],
            });
        },

        async _fetch(limit, offset) {
            console.log("## Fetch ##")
            
            var tipo_orden_filtro = $('.tipo_orden_filtro').val();
            console.log("Is checked: ")
            console.log(is_checked)

            console.log("## Orders ##")
            const sale_orders = await this._getOrderIdsForCurrentPage(limit, offset);
            console.log(sale_orders)
            
            sale_orders.map(element => {
                element.model = 'sale';
            })
            
            console.log(sale_orders)
            console.log("## Repairs ##")
            
            const sale_repairs = await this._getRepairsIdsForCurrentPage(limit, offset);
            console.log(sale_repairs)
            sale_repairs.map(element => {
                element.date_order = element.schedule_date;
                element.model = 'repair';      
                delete element.schedule_date;
                return element;
            })
            console.log(sale_repairs)
            var sale_orders_real = sale_orders//.concat(sale_repairs)
            if (tipo_orden_filtro == 'repair'){
                sale_orders_real = sale_repairs
            }
            // var sale_orders_real = sale_orders.concat(sale_repairs)
            console.log("Total Orders")
            console.log(sale_orders_real)
            this.totalCount = sale_orders_real.length;
            console.log( this.totalCount)
            return sale_orders_real;
        }

    });
});