/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";


/**
 * Brands Mega Menu Widget
 * Handles dynamic loading of brands content in the mega menu
 */
const BrandsMegaMenuWidget = publicWidget.Widget.extend({
    selector: '#brands-mega-menu-content',

    /**
     * Widget initialization
     */
    start: function () {
        this._super.apply(this, arguments);
        this._loadBrandsContent();
        return Promise.resolve();
    },

    /**
     * Load brands content via AJAX
     * @private
     */
    _loadBrandsContent: function () {
        const self = this;

        // Show loading state
        this._showLoadingState();

        // Make AJAX request
        fetch('/brands/mega-menu')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.text();
            })
            .then(html => {
                self._renderContent(html);
            })
            .catch(error => {
                console.error('Error loading brands mega menu:', error);
                self._showErrorState(error.message);
            });
    },

    /**
     * Show loading state
     * @private
     */
    _showLoadingState: function () {
        this.$el.html(`
            <div class="col-12 text-center py-4">
                <i class="fa fa-spinner fa-spin me-2"></i>
                Loading brands...
            </div>
        `);
    },

    /**
     * Show error state
     * @private
     */
    _showErrorState: function (errorMessage) {
        this.$el.html(`
            <div class="col-12 text-center py-4">
                <div class="alert alert-warning">
                    <i class="fa fa-exclamation-triangle me-2"></i>
                    Error loading brands: ${errorMessage}
                </div>
                <button class="btn btn-sm btn-outline-primary" onclick="location.reload()">
                    <i class="fa fa-refresh me-1"></i>
                    Retry
                </button>
            </div>
        `);
    },

    /**
     * Render the loaded content
     * @private
     */
    _renderContent: function (html) {
        this.$el.html(html);
    },
});

// Register the widget
publicWidget.registry.BrandsMegaMenuWidget = BrandsMegaMenuWidget;

export default BrandsMegaMenuWidget;
