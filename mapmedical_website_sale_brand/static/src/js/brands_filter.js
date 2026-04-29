/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";


publicWidget.registry.BrandsFilter = publicWidget.Widget.extend({
    selector: '.js_brands_filter',
    events: {
        'change .js_brand_checkbox': '_onBrandChange',
    },

    /**
     * Handle brand checkbox change
     */
    _onBrandChange: function (ev) {
        // Small delay to allow multiple rapid changes
        clearTimeout(this._brandChangeTimeout);
        this._brandChangeTimeout = setTimeout(() => {
            this._submitForm();
        }, 300);
    },

    /**
     * Submit the form with current filter state
     */
    _submitForm: function () {
        const form = this.el;
        const formData = new FormData(form);
        const params = new URLSearchParams();

        // Add all form data to URL parameters
        for (let [key, value] of formData.entries()) {
            if (value) {
                params.append(key, value);
            }
        }

        // Navigate to the new URL
        const currentUrl = window.location.pathname;
        const newUrl = `${currentUrl}?${params.toString()}`;
        window.location.href = newUrl;
    },
});
