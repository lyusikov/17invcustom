/** @odoo-module */

import { registry } from "@web/core/registry";


registry.category("web_tour.tours").add("website_tour_check_product_page_customizations", {
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
            "trigger": "span.oe_currency_value",
            "content": "Check price visibility",
            "isCheck": true,
        },
        {
            "trigger": "div.o_product_unique_reference:contains('SKU Number: <test_unique_reference>!')",
            "content": "Check unique reference",
        },
        // the next 4 steps are checking alert for an unlogged user that contains two links
        // (Log in or create an account to proceed with checkout.)
        {
            "trigger": "a.o_unlogged_alert_text[href='/web/login']:contains('Log in')",
            "content": "Check <Log in> link",
            "isCheck": true,
        },
        {
            "trigger": "span.o_unlogged_alert_text:contains('or')",
            "content": "Check <or> text",
            "isCheck": true,
        },
        {
            "trigger": "a.o_unlogged_alert_text[href='/web/signup']:contains('create an account')",
            "content": "Check <create an account> link",
            "isCheck": true,
        },
        {
            "trigger": "span.o_unlogged_alert_text:contains('to proceed with checkout.')",
            "content": "Check <to proceed with checkout.> text",
            "isCheck": true,
        }
    ],
});
