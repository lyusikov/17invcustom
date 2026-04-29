# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettingsSEOExtension(models.TransientModel):
    _inherit = 'res.config.settings'

    seo_use_product_tags = fields.Boolean(
        string='Use Product Tags for SEO Rules',
        config_parameter='kw_seo_configuration_ext.use_product_tags',
        help='Enable SEO rules matching by product tags in addition to categories and attributes.',
    )
