{
    "name": "Map-Medical Website eCommerce Brand",
    "version": "17.0.0.1.0",
    "category": "Hidden",
    "description": """Map-Medical Website eCommerce Brand""",
    "depends": [
        "website_sale",
        "mapmedical_base",
        "mapmedical_sale_stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_brand_category_sequence_views.xml",
        "views/product_manufacturer_views.xml",
        "views/res_config_settings_views.xml",
        "views/website_brand_templates.xml",
        "views/product_template_views.xml",
        "data/ir_actions_server.xml",
        "data/base_automation.xml",
        "data/website_menu_data.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "mapmedical_website_sale_brand/static/src/js/brands_filter.js",
            "mapmedical_website_sale_brand/static/src/js/brands_mega_menu.js",
            "mapmedical_website_sale_brand/static/src/css/brands_mega_menu.css",
            "mapmedical_website_sale_brand/static/src/css/brands_page.css",
        ],
    },
    "author": "Map-Medical",
    "maintainer": ["Itransition"],
    "license": "LGPL-3",
}
