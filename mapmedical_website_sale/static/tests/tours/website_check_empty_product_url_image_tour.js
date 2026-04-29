/** @odoo-module */

import { registry } from "@web/core/registry";


registry.category("web_tour.tours").add("website_tour_check_empty_url_image_in_website", {
    url: "/",
    test: true,
    sequence: 100,
    steps: () => [
        {
            "trigger": "a[href='/shop']",
            "content": "Go to shop page",
        },
        {
            "trigger": ".o_wsale_products_grid_table_wrapper .oe_product_image_img_wrapper > img[src='/product/static/img/placeholder_thumbnail.png']",
            "content": "Check Url Image",
            "run": () => {},
        },
    ],
});
