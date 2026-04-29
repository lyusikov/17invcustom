# -*- coding: utf-8 -*-
{
    'name': "kw_seo_configuration",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'author': "Kitworks",
    'website': "https://kitworks.systems/",

    'category': 'website',
    'license': 'OPL-1',
    'version': '17.0.0.0.6',

    # any module necessary for this one to work correctly
    'depends': ['base', 'website', 'website_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/seo_model_views.xml',
        'views/seo_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'kw_seo_configuration/static/src/scss/custom_styles.scss'
        ],
    },
    'price': 100,
    'installable': True,
    'application': False,
    'auto_install': False,
}
