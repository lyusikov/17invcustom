# -*- coding: utf-8 -*-
{
    'name': 'KW SEO Configuration Extension',
    'summary': 'Extension for kw_seo_configuration: add extra SEO fields and settings',
    'author': 'Kitworks',
    'website': 'https://kitworks.systems/',
    'category': 'website',
    'license': 'OPL-1',
    'version': '17.0.0.1.0',
    'depends': [
        'base',
        'website',
        'website_sale',
        'product',
        'kw_seo_configuration',
    ],
    'data': [
        'views/seo_model_extension_views.xml',
        'views/seo_config_settings_extension_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
