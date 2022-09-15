
odoo.define('pos_customs_sale_order.SaleOrderFetcher', function (require) {
    'use strict';

    const { patch } = require('web.utils');

    // console.log(patch)
    // console.log("OVERRIDE")
    // const Registries = require('point_of_sale.Registries');
    const SaleOrderFetcher = require('pos_sale.SaleOrderFetcher');
    

    patch(SaleOrderFetcher, "static patch", {
        async _getOrderIdsForCurrentPage(limit, offset) {
            // console.log("SSSSS")
            // console.log("LOADEDDDD")
            // console.log(this)
            // console.log(this.searchDomain)
            // console.log(this.comp.env.pos.config)
            // console.log(this.comp.env.pos.config.crm_team_id)

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

            return await this.rpc({
                model: 'sale.order',
                method: 'search_read',
                args: [this.searchDomain ? this.searchDomain : [], ['name', 'partner_id', 'amount_total', 'date_order', 'state', 'user_id', 'team_id'], offset, limit],
                context: this.comp.env.session.user_context,
            });
        },
      });
    
});

