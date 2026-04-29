/** @odoo-module */

import { registry } from "@web/core/registry";


registry.category("web_tour.tours").add("website_tour_check_removing_caregory_param_for_breadcrumbs", {
    url: "/",
    test: true,
    sequence: 100,
    steps: () => [
        {
            "trigger": "a[href='/shop']",
            "content": "Go to shop page",
        },
        {
            "trigger": "li[data-link-href='/shop/category/desks-1']",
            "content": "Select 'Desks' category",
        },
        {
            "trigger": ".oe_product_cart a:contains('Customizable Desk')",
            "content": "Open 'Customizable Desk' product page",
        },
        {
            "content": "Check 'category' param in URI",
            "trigger": "span.oe_currency_value",
            "run": () => {
                const categoryParam = "?category=1";
                const currentSearch = window.location.search;
                if (currentSearch === categoryParam) {
                    throw new Error(`${categoryParam} shouldn't be in URI!`);
                }
            },
        },
    ],
});
