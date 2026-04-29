/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
import { renderToFragment } from "@web/core/utils/render";

publicWidget.registry.DynamicSnippet = publicWidget.Widget.extend({
    selector: ".product_category_snippet_section",
    events: Object.assign({
        "click .o_category": "_onCategoryClick",
    }, publicWidget.Widget.events),

    CATEGORY_ACTIVE_CLASS: "o_category_active", // style-class for active opened category

    start: function () {
        const def = this._super.apply(this, arguments);
        const self = this;
        const element = document.getElementsByClassName("o_categories_items")[0];
        element.innerHTML = "";
        jsonrpc("/shop/get_category", {}).then((data) => {
            self.data = data["data"];
            element.appendChild(renderToFragment("mapmedical_website_sale.WebsiteCategoryItems", data));
            this.lastSubcategoryElement = null;
        });
        return def;
    },

    _onCategoryClick: function(ev) {
        const subcategoriesRootElement = document.getElementsByClassName("o_subcategories_root")[0];
        const subcatgoriesItemsElement = subcategoriesRootElement.getElementsByClassName("o_subcategories_items")[0];
        const target = ev.currentTarget;

        // getting child categories
        const subCategoriesData = this.data.filter((item) => item["id"] == target.dataset.id)[0]["child_ids"];

        // if page has active opened category need to remove active style-class for category
        if (this.lastSubcategoryElement) {
            this.lastSubcategoryElement.classList.remove(this.CATEGORY_ACTIVE_CLASS);
        }
        // need to reset active category and hide child categories block if
        // category without child categories or active category(open -> close) has been selected
        if (subCategoriesData.length < 1 || this.lastSubcategoryElement === target) {
            this.lastSubcategoryElement = null;
            subcategoriesRootElement.classList.add("d-none");
        } else {
            // otherwise, mark current category as active and save it
            target.classList.add(this.CATEGORY_ACTIVE_CLASS);
            this.lastSubcategoryElement = target;
            subcatgoriesItemsElement.innerHTML = "";
            // load child categories into block
            subcatgoriesItemsElement.appendChild(renderToFragment("mapmedical_website_sale.WebsiteSubcategoryItems", {"data": subCategoriesData}));
            // show them and reset marginTop before recomputing adaptive position and size
            subcategoriesRootElement.classList.remove("d-none");
            subcategoriesRootElement.style.marginTop = 0;

            const categoriesElement = document.getElementsByClassName("o_product_category_snippet_root")[0];
            const categoriesTitleElement = categoriesElement.getElementsByClassName("title")[0];

            // get size and positions for blocks to help recomputing adaptive position and size
            const categoriesRect = categoriesElement.getBoundingClientRect();
            const selectedCategoryRect = target.getBoundingClientRect();
            const subcategoriesRect = subcategoriesRootElement.getBoundingClientRect();
            const categoriesTitleElementRect = categoriesTitleElement.getBoundingClientRect();

            // position and size computing
            let initialMargin = selectedCategoryRect.y - subcategoriesRect.y - 5;
            const potentialY = initialMargin + subcategoriesRect.height;
            if (potentialY > categoriesRect.height) {
                const diff = potentialY - categoriesRect.height;
                initialMargin -= diff;
            }
            const paddingBottom = parseInt(window.getComputedStyle(categoriesElement).paddingBottom.replace("px", "")) / 2;
            const maxHeight = categoriesRect.height - categoriesTitleElementRect.height - paddingBottom;

            // set computed values
            subcatgoriesItemsElement.style.maxHeight = `${maxHeight}px`;
            subcategoriesRootElement.style.marginTop = `${initialMargin}px`;
        }
    },
});

export default publicWidget.registry.DynamicSnippet;
