odoo.define('pos_customs.pos_invoice_datas', function (require) {
    "use strict";
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { useState, useRef } = owl.hooks;

    class SetInvoiceInfoPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({inputValue: this.props.startingValue});
            this.inputRef = useRef('input');
            this.changes = {};
        }

        getPayload() {
            return this.state.inputValue;
        }

        async captureCfdiData(event) {
            console.log("____ SENDING INVOICE INFO.. ");
            /*var order = this.env.pos.get('selectedOrder');
            if (order.get_client() != null) {
                order.wv_note = $(".wv_note").val();
                //////console.log("note",order);

                //console.log("print note",order.wv_note);
                // await this.save_order();

                //  await this.save_order();
                await this.trigger('close-popup');

            } else {
                alert("Customer is required for sale order. Please select customer first !!!!");
            }
            // this.cancel();*/
        }



    }

    SetInvoiceInfoPopupWidget.template = 'SetInvoiceInfoPopupWidget';
    Registries.Component.add(SetInvoiceInfoPopupWidget);
    SetInvoiceInfoPopupWidget.defaultProps = {
        confirmText: 'Aceptar',
        cancelText: 'Cancelar',
        title: 'Selecciona parametros de facturación',
        body: '',
    }

});