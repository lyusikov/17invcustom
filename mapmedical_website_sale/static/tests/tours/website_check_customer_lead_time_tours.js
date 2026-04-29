/** @odoo-module */

import { registry } from "@web/core/registry";
import tourUtils from "@website/js/tours/tour_utils";
import wsTourUtils from "@website_sale/js/tours/tour_utils";


const productsSnippet = {id: "s_dynamic_snippet_products", name: "Products"};
const template = "dynamic_filter_template_product_product_view_detail";


function changeTemplate(templateKey) {
    const templateClass = templateKey.replace(/dynamic_filter_template_/, "s_");
    const optionBlock = "dynamic_snippet_products";
    return [
        tourUtils.changeOption(optionBlock, 'we-select[data-name="template_opt"] we-toggler', "template"),
        tourUtils.changeOption(optionBlock, `we-button[data-select-data-attribute="website_sale.${templateKey}"]`),
        {
            content: "Check the template is applied",
            trigger: `iframe .s_dynamic_snippet_products.${templateClass} .carousel`,
            run: () => null,
        },
    ];
}

// enable dynamic filter snipper to check customer_lead_time in tours below
tourUtils.registerWebsitePreviewTour("website_tour_add_dynamic_filter_template_product", {
    test: true,
    url: "/",
    edition: true,
},
() => {
    return [
        tourUtils.dragNDrop(productsSnippet),
        tourUtils.clickOnSnippet(productsSnippet),
        ...changeTemplate(template),
        ...tourUtils.clickOnSave(),
    ]
});

const commonCustomerLeadTimeSteps = [
    {
        "trigger": ".o_carousel_product_card .o_product_customer_lead_time > span:contains('24 Hours')",
        "content": "Check customer lead time value in products snippet carousel",
        "run": () => {},
    },
    {
        "trigger": "a[href='/shop']",
        "content": "Go to shop page",
    },
    {
        "trigger": ".o_wsale_products_grid_table_wrapper .o_product_customer_lead_time > span:contains('24 Hours')",
        "content": "Check customer lead time value in shop grid",
        "run": () => {},
    },
    {
        "trigger": "i.oi-view-list",
        "content": "Switch to list mode",
    },
    {
        "trigger": ".o_wsale_layout_list .o_product_customer_lead_time > span:contains('24 Hours')",
        "content": "Check customer lead time value in shop list",
        "run": () => {},
    },
    {
        "trigger": ".oe_product_cart a:contains('Chair floor protection')",
        "content": "Open 'Chair floor protection' product page",
    },
    {
        "trigger": "#product_details .o_product_customer_lead_time > span:contains('24 Hours')",
        "content": "Check customer lead time value in product page",
        "run": () => {},
    }
]

registry.category("web_tour.tours").add("website_tour_check_customer_lead_time_in_website_for_not_logged_in_user", {
    url: "/",
    test: true,
    sequence: 100,
    steps: () => [
        ...commonCustomerLeadTimeSteps,
    ],
});

registry.category("web_tour.tours").add("website_tour_check_customer_lead_time_in_website_for_logged_in_user", {
    url: "/",
    test: true,
    sequence: 100,
    steps: () => [
        ...commonCustomerLeadTimeSteps,
        {
            "trigger": "#add_to_cart",
            "content": "Add product to cart",
        },
        wsTourUtils.goToCart(1),
        {
            "trigger": ".o_cart_product .o_product_customer_lead_time > span:contains('24 Hours')",
            "content": "Check customer lead time value in cart",
            "run": () => {},
        },
    ],
});
