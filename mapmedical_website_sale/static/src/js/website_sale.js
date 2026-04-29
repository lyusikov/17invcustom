/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import "@website_sale/js/website_sale";

const WebsiteSale = publicWidget.registry.WebsiteSale;

WebsiteSale.include({
    events: Object.assign({
        "change #purchase_order_number": "_onChangePurchaseOrderNumber",
        "change #customer_notes": "_onChangeCustomerNotes",
    }, WebsiteSale.prototype.events),

    /**
     * Event handler for the change event on the purchase order number input field.
     * Calls the method to save the client order reference.
     *
     * @private
     */
    _onChangePurchaseOrderNumber: async function () {
        await this._saveClientOrderRef();
    },

    /**
     * Event handler for the change event on the customer notes textarea.
     * Calls the method to save the customer notes.
     *
     * @private
     */
    _onChangeCustomerNotes: async function () {
        await this._saveCustomerNotes();
    },

    /**
     * Saves the client order reference.
     * Retrieves the value from the purchase order number input field and sends it to the server.
     *
     * @private
     * @returns {Promise} The result of the RPC call.
     */
    _saveClientOrderRef: async function () {
        const purchaseOrderNumber = $("#purchase_order_number").val();
        return await this.rpc("/shop/update_client_order_ref", {
            "purchase_order_number": purchaseOrderNumber,
        });
    },

    /**
     * Saves the customer notes by making an RPC call to the server.
     * Retrieves the value from the customer notes textarea and sends it to the server.
     *
     * @private
     * @returns {Promise} The result of the RPC call.
     */
    _saveCustomerNotes: async function () {
        const customerNotes = $("#customer_notes").val();
        return await this.rpc("/shop/update_customer_notes", {
            "customer_notes": customerNotes,
        });
    }
});
