odoo.define('q_pdv_orders_repair.SaleOrderRow', function (require) {
    "use strict";

    const { Component } = require('point_of_sale.Registries');
    const SaleOrderRow = require('pos_sale.SaleOrderRow');

    const SaleOrder = SaleOrderRow => class extends SaleOrderRow{
        get state() {
            let state_mapping = {
              'draft': this.env._t('Quotation'),
              'sent': this.env._t('Quotation Sent'),
              'sale': this.env._t('Sales Order'),
              'done': this.env._t('Locked'),
              'cancel': this.env._t('Cancelled'),
              'ready': this.env._t('Ready'),
              'under_repair': this.env._t('Under Repair'),
              '2binvoiced': this.env._t('For invoiced'),
            };
            return state_mapping[this.order.state];
        }
    }

    Component.extend(SaleOrderRow, SaleOrder)
    return SaleOrder;
});