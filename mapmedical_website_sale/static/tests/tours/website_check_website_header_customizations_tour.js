/** @odoo-module */

import { registry } from "@web/core/registry";
import tourUtils from "@website/js/tours/tour_utils";


const CART_ICON_WITH_TEXT = "a:contains('My Cart')";


// apply 'Menu - Sales 2' template for website header
tourUtils.registerWebsitePreviewTour("website_tour_apply_header_template_menu_sales_2", {
    test: true,
    url: "/",
    edition: true,
},
() => {
    return [
        tourUtils.selectHeader(),
        tourUtils.changeOption("HeaderLayout", 'we-select[data-variable="header-template"] we-toggler'),
        tourUtils.changeOption("HeaderLayout", 'we-button[data-name="header_sales_two_opt"]'),
        ...tourUtils.clickOnSave(),
    ]
});


registry.category("web_tour.tours").add("website_tour_check_website_header_customizations_for_not_logged_in_user", {
    url: "/",
    test: true,
    sequence: 100,
    steps: () => [
        {
            "trigger": "#wrapwrap",
            "content": "Check that 'My Cart' text is hidden",
            "run": () => {
                if ($(CART_ICON_WITH_TEXT).length) {
                    throw new Error("Cart icon should be without 'My Cart' text");
                }
            },
        },
    ],
});

registry.category("web_tour.tours").add("website_tour_check_website_header_customizations_for_logged_in_user", {
    url: "/",
    test: true,
    sequence: 100,
    steps: () => [
        {
            "trigger": CART_ICON_WITH_TEXT,
            "content": "Check that 'My Cart' text isn't hidden",
            "isCheck": true,
        },
    ],
});
