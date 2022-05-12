/* global Backbone, waitForWebfonts */
odoo.define('q_pdv_orders_repair.SaleOrderManagementScreen', function (require) {
    "use strict";
    const SaleOrderManagementScreen = require('pos_sale.SaleOrderManagementScreen')
    const { sprintf } = require('web.utils');
    const { parse } = require('web.field_utils');
    const { useContext } = owl.hooks;
    const { useListener } = require('web.custom_hooks');
    const ControlButtonsMixin = require('point_of_sale.ControlButtonsMixin');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const Registries = require('point_of_sale.Registries');
    const SaleOrderFetcher = require('pos_sale.SaleOrderFetcher');
    const IndependentToOrderScreen = require('point_of_sale.IndependentToOrderScreen');
    const contexts = require('point_of_sale.PosContext');
    const models = require('point_of_sale.models');
    const { Component } = require('point_of_sale.Registries');
    
    //COPIA LOS ATRIBUTOS // DUPLICADO DE LA CLASE
    const OrderButtonSet = SaleOrderManagementScreen => class extends SaleOrderManagementScreen{

        async _getSOLines_repair(ids) {
            let so_lines = await this.rpc({
                model: 'repair.line',
                method: 'read_converted',
                args: [ids],
                context: this.env.session.user_context,
            });
            return so_lines;
          }

        async _getSOLines_repair_fees(ids) {
            let so_lines = await this.rpc({
                model: 'repair.fee',
                method: 'read_converted',
                args: [ids],
                context: this.env.session.user_context,
            });
            return so_lines;
          }
        
          async _getSaleOrder_repair(id) {
            let sale_order = await this.rpc({
                model: 'repair.order',
                method: 'read',
                args: [[id],['fees_lines', 'operations', 'partner_id', 'pricelist_id', 'amount_total', 'amount_untaxed', 'product_id', 'lot_id', 'product_qty']],
              });
            
            let sale_lines = await this._getSOLines_repair(sale_order[0].operations);
            let sale_lines_fees = await this._getSOLines_repair_fees(sale_order[0].fees_lines);
            var lines = sale_lines_fees.concat(sale_lines)
            sale_order[0].order_line = lines;
            return sale_order[0];
        }
        
        async _onClickSaleOrder(event) {
            const clickedOrder = event.detail;
            if (clickedOrder.model == "repair"){
                const { confirmed, payload: selectedOption } = await this.showPopup('SelectionPopup',
                {
                    title: this.env._t('What do you want to do?'),
                    list: [{id:"0", label: this.env._t("Apply a down payment"), item: false}, {id:"1", label: this.env._t("Settle the order"), item: true}],
                });

                if(confirmed){
                    let currentPOSOrder = this.env.pos.get_order();
                    let sale_order = await this._getSaleOrder_repair(clickedOrder.id);
                    
                    try {
                      await this.env.pos.load_new_partners();
                    }
                    catch (error){
                    }
                    currentPOSOrder.set_client(this.env.pos.db.get_partner_by_id(sale_order.partner_id[0]));
                    let orderFiscalPos = sale_order.fiscal_position_id ? this.env.pos.fiscal_positions.find(
                        (position) => position.id === sale_order.fiscal_position_id[0]
                    )
                    : false;
                    if (orderFiscalPos){
                        currentPOSOrder.fiscal_position = orderFiscalPos;
                    }
                    let orderPricelist = sale_order.pricelist_id ? this.env.pos.pricelists.find(
                        (pricelist) => pricelist.id === sale_order.pricelist_id[0]
                    )
                    : false;
                    if (orderPricelist){
                        currentPOSOrder.set_pricelist(orderPricelist);
                    }

                    currentPOSOrder.set_repair(sale_order.id)
      
                    if (selectedOption){
                      // settle the order
                      let lines = sale_order.order_line;
                      let product_to_add_in_pos = this.env.pos.db.get_product_by_id(sale_order.product_id[0])
                      if (product_to_add_in_pos.length){
                          const { confirmed } = await this.showPopup('ConfirmPopup', {
                              title: this.env._t('Products not available in POS'),
                              body:
                                  this.env._t(
                                      'Some of the products in your Sale Order are not available in POS, do you want to import them?'
                                  ),
                              confirmText: this.env._t('Yes'),
                              cancelText: this.env._t('No'),
                          });
                          if (confirmed){
                              await this.env.pos._addProducts(product_to_add_in_pos);
                          }
      
                      }
      
                      let useLoadedLots;
      
                      for (var i = 0; i < lines.length; i++) {
                          let line = lines[i];
                          if (!this.env.pos.db.get_product_by_id(line.product_id[0])){
                              continue;
                          }
                          let new_line = new models.Orderline({}, {
                              pos: this.env.pos,
                              order: this.env.pos.get_order(),
                              product: this.env.pos.db.get_product_by_id(line.product_id[0]),
                              description: line.name,
                              price: line.price_total,
                              tax_ids: orderFiscalPos ? undefined : line.tax_id,
                              price_manually_set: true,
                              ref_repair: this.ref_repair,
                              sale_order_origin_id: clickedOrder,
                          });

                          console.log(new_line)
      
                          if (
                              new_line.get_product().tracking !== 'none' &&
                              (this.env.pos.picking_type.use_create_lots || this.env.pos.picking_type.use_existing_lots) &&
                              line.lot_id.length > 0
                          ) {
                              // Ask once when `useLoadedLots` is undefined, then reuse it's value on the succeeding lines.
                              const { confirmed } =
                                  useLoadedLots === undefined
                                      ? await this.showPopup('ConfirmPopup', {
                                            title: this.env._t('SN/Lots Loading'),
                                            body: this.env._t(
                                                'Do you want to load the SN/Lots linked to the Sales Order?'
                                            ),
                                            confirmText: this.env._t('Yes'),
                                            cancelText: this.env._t('No'),
                                        })
                                      : { confirmed: useLoadedLots };
                              useLoadedLots = confirmed;
                              if (useLoadedLots) {
                                  var lots = [line.lot_id[1]]
                                  new_line.setPackLotLinesRepair({
                                      modifiedPackLotLines: [],
                                      newPackLotLines: (lots),
                                  });
                              }
                          }
                          //new_line.setQuantityFromSOL(line.product_uom_qty);
                          new_line.set_unit_price(line.price_total);
                          new_line.set_discount(line.discount);
                          this.env.pos.get_order().add_orderline(new_line);
                      }
                    }
                    else {
                      // apply a downpayment
                      if (this.env.pos.config.down_payment_product_id){
      
                          let lines = sale_order.order_line;
                          let tab = [];
      
                          for (let i=0; i<lines.length; i++) {
                              tab[i] = {
                                  'product_name': lines[i].product_id[1],
                                  'product_uom_qty': lines[i].product_uom_qty,
                                  'price_unit': lines[i].price_unit,
                                  'total': lines[i].price_total,
                              };
                          }
                          let down_payment_product = this.env.pos.db.get_product_by_id(this.env.pos.config.down_payment_product_id[0])
                          let down_payment_tax = this.env.pos.taxes_by_id[down_payment_product.taxes_id]
                          let down_payment = down_payment_tax.price_include ? sale_order.amount_total : sale_order.amount_untaxed;
      
                          const { confirmed, payload } = await this.showPopup('NumberPopup', {
                              title: sprintf(this.env._t("Percentage of %s"), this.env.pos.format_currency(sale_order.amount_total)),
                              startingValue: 0,
                          });
                          if (confirmed){
                              down_payment = down_payment * parse.float(payload) / 100;
                          }
      
                          let new_line = new models.Orderline({}, {
                              pos: this.env.pos,
                              order: this.env.pos.get_order(),
                              product: down_payment_product,
                              price: down_payment,
                              price_manually_set: true,
                              sale_order_origin_id: clickedOrder,
                              down_payment_details: tab,
                          });
    
                          new_line.set_unit_price(down_payment);
                          this.env.pos.get_order().add_orderline(new_line);
                      }
                      else {
                          const title = this.env._t('No down payment product');
                          const body = this.env._t(
                              "It seems that you didn't configure a down payment product in your point of sale.\
                              You can go to your point of sale configuration to choose one."
                          );
                          await this.showPopup('ErrorPopup', { title, body });
                      }
                    }
      
                    currentPOSOrder.trigger('change');
                    this.close();
                  }
            }
            else{
                const { confirmed, payload: selectedOption } = await this.showPopup('SelectionPopup',
                {
                    title: this.env._t('What do you want to do?'),
                    list: [{id:"0", label: this.env._t("Apply a down payment"), item: false}, {id:"1", label: this.env._t("Settle the order"), item: true}],
                });

                if(confirmed){
                let currentPOSOrder = this.env.pos.get_order();
                let sale_order = await this._getSaleOrder(clickedOrder.id);
                try {
                    await this.env.pos.load_new_partners();
                }
                catch (error){
                }
                currentPOSOrder.set_client(this.env.pos.db.get_partner_by_id(sale_order.partner_id[0]));
                let orderFiscalPos = sale_order.fiscal_position_id ? this.env.pos.fiscal_positions.find(
                    (position) => position.id === sale_order.fiscal_position_id[0]
                )
                : false;
                if (orderFiscalPos){
                    currentPOSOrder.fiscal_position = orderFiscalPos;
                }
                let orderPricelist = sale_order.pricelist_id ? this.env.pos.pricelists.find(
                    (pricelist) => pricelist.id === sale_order.pricelist_id[0]
                )
                : false;
                if (orderPricelist){
                    currentPOSOrder.set_pricelist(orderPricelist);
                }

                if (selectedOption){
                    // settle the order
                    let lines = sale_order.order_line;
                    let product_to_add_in_pos = lines.filter(line => !this.env.pos.db.get_product_by_id(line.product_id[0])).map(line => line.product_id[0]);
                    if (product_to_add_in_pos.length){
                        const { confirmed } = await this.showPopup('ConfirmPopup', {
                            title: this.env._t('Products not available in POS'),
                            body:
                                this.env._t(
                                    'Some of the products in your Sale Order are not available in POS, do you want to import them?'
                                ),
                            confirmText: this.env._t('Yes'),
                            cancelText: this.env._t('No'),
                        });
                        if (confirmed){
                            await this.env.pos._addProducts(product_to_add_in_pos);
                        }

                    }
                    
                    let useLoadedLots;

                    for (var i = 0; i < lines.length; i++) {
                        let line = lines[i];
                        if (!this.env.pos.db.get_product_by_id(line.product_id[0])){
                            continue;
                        }

                        let new_line = new models.Orderline({}, {
                            pos: this.env.pos,
                            order: this.env.pos.get_order(),
                            product: this.env.pos.db.get_product_by_id(line.product_id[0]),
                            description: line.name,
                            price: line.price_unit,
                            tax_ids: orderFiscalPos ? undefined : line.tax_id,
                            price_manually_set: true,
                            sale_order_origin_id: clickedOrder,
                            sale_order_line_id: line,
                            customer_note: line.customer_note,
                        });
                        console.log(new_line)
                        if (
                            new_line.get_product().tracking !== 'none' &&
                            (this.env.pos.picking_type.use_create_lots || this.env.pos.picking_type.use_existing_lots) &&
                            line.lot_names.length > 0
                        ) {
                            // Ask once when `useLoadedLots` is undefined, then reuse it's value on the succeeding lines.
                            const { confirmed } =
                                useLoadedLots === undefined
                                    ? await this.showPopup('ConfirmPopup', {
                                        title: this.env._t('SN/Lots Loading'),
                                        body: this.env._t(
                                            'Do you want to load the SN/Lots linked to the Sales Order?'
                                        ),
                                        confirmText: this.env._t('Yes'),
                                        cancelText: this.env._t('No'),
                                    })
                                    : { confirmed: useLoadedLots };
                            useLoadedLots = confirmed;
                            if (useLoadedLots) {
                                var lots = (line.lot_names || []).map((name) => ({ lot_name: name }))
                                new_line.setPackLotLines({
                                    modifiedPackLotLines: [],
                                    newPackLotLines: (lots),
                                });
                            }
                        }
                        new_line.setQuantityFromSOL(line);
                        new_line.set_unit_price(line.price_unit);
                        new_line.set_discount(line.discount);
                        this.env.pos.get_order().add_orderline(new_line);
                    }
                }
                else {
                    // apply a downpayment
                    if (this.env.pos.config.down_payment_product_id){

                        let lines = sale_order.order_line;
                        let tab = [];

                        for (let i=0; i<lines.length; i++) {
                            tab[i] = {
                                'product_name': lines[i].product_id[1],
                                'product_uom_qty': lines[i].product_uom_qty,
                                'price_unit': lines[i].price_unit,
                                'total': lines[i].price_total,
                            };
                        }
                        let down_payment_product = this.env.pos.db.get_product_by_id(this.env.pos.config.down_payment_product_id[0])
                        let down_payment_tax = this.env.pos.taxes_by_id[down_payment_product.taxes_id]
                        let down_payment = down_payment_tax.price_include ? sale_order.amount_total : sale_order.amount_untaxed;

                        const { confirmed, payload } = await this.showPopup('NumberPopup', {
                            title: sprintf(this.env._t("Percentage of %s"), this.env.pos.format_currency(sale_order.amount_total)),
                            startingValue: 0,
                        });
                        if (confirmed){
                            down_payment = down_payment * parse.float(payload) / 100;
                        }


                        let new_line = new models.Orderline({}, {
                            pos: this.env.pos,
                            order: this.env.pos.get_order(),
                            product: down_payment_product,
                            price: down_payment,
                            price_manually_set: true,
                            sale_order_origin_id: clickedOrder,
                            down_payment_details: tab,
                        });
                        new_line.set_unit_price(down_payment);
                        this.env.pos.get_order().add_orderline(new_line);
                    }
                    else {
                        const title = this.env._t('No down payment product');
                        const body = this.env._t(
                            "It seems that you didn't configure a down payment product in your point of sale.\
                            You can go to your point of sale configuration to choose one."
                        );
                        await this.showPopup('ErrorPopup', { title, body });
                    }
                }

                currentPOSOrder.trigger('change');
                this.close();
                }
            }
            
        }

    }

    Component.extend(SaleOrderManagementScreen, OrderButtonSet)

    return OrderButtonSet;

});