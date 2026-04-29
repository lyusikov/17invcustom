/** @odoo-module **/

import { OptionalProductsModal } from "@website_sale_product_configurator/js/sale_product_configurator_modal";

OptionalProductsModal.include({
    /**
    * Disable of existing function to avoid image changing
    */
    _updateProductImage: function ($productContainer, displayImage, productId, productTemplateId) {},

    /**
    * Extention to keep the first image
    *
    */
    _postProcessContent: function ($modalContent) {
        const imgUrl = $modalContent.find("img:first").attr("src");
        const $res = this._super.apply(this, arguments);
        if ($res) {
            $res.find("img:first").attr("src", imgUrl);
        }
        return $res;
    },
});
