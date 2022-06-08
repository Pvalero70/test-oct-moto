odoo.define('credit_note_restrict.RefundButtonHide', function (require) {
    'use strict';

    const ButtonRefund = require('point_of_sale.RefundButton');
    const Registries = require('point_of_sale.Registries');


    const POSRefundButtonCustomHide = (ButtonRefund) =>
        class extends ButtonRefund {
            constructor() {


                super(...arguments);
                var session = require('web.session');



                session.user_has_group('credit_note_restrict.credit_note_pos_group').then(function(has_group) {
                    if(has_group) {

                    } else {
                        try {
                          $('document').ready(function(){
                            var button = document.getElementsByClassName("fa fa-undo");
                                if (button.length > 0) {
                                    button = button[0];
                                    if ( typeof(button) != 'undefined'){
                                        if( typeof(button.parentElement) != 'undefined'){
                                            button.parentElement.style.visibility = "hidden";
                                        }
                                    }

                                }

                            });
                        } catch (error) {
                          console.error(error);

                        }
                    }
                });




            }
        };

    Registries.Component.extend(ButtonRefund, POSRefundButtonCustomHide);

    return ButtonRefund;
});