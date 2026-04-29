/** @odoo-module */

import { registry } from "@web/core/registry";
import tourUtils from "@website/js/tours/tour_utils";


// enable left-side categories bar to check in tour below
tourUtils.registerWebsitePreviewTour("website_tour_add_left_side_categories_bar", {
    test: true,
    url: "/shop",
    edition: true,
},
() => {
    return [
        {
            content: "Open Customize tab",
            trigger: ".o_we_customize_snippet_btn",
        },
        tourUtils.changeOption("WebsiteSaleGridLayout", 'we-button[data-name="categories_opt"]'),
        ...tourUtils.clickOnSave(),
    ]
});

registry.category("web_tour.tours").add("website_tour_check_categories_snippet_dom", {
    url: "/",
    test: true,
    sequence: 100,
    steps: () => [
        {
            "trigger": "a[href='/shop']",
            "content": "Go to shop page",
        },
        {
            "trigger": "a.form-check.d-inline-block.ps-4 label:contains(All Products)",
            "content": "Check 'All Products' link is '<a>' element",
            "isCheck": true,
        },
        {
            "trigger": "a.form-check.d-inline-block.ps-4 label:contains(Desks)",
            "content": "Check 'Desks' link is '<a>' element",
            "isCheck": true,
        },
    ],
});
