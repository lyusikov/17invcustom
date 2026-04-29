# -*- coding: utf-8 -*-

from odoo import models, fields


class SEOModelExtension(models.Model):
    _inherit = 'seo.model'

    seo_text = fields.Html(
        string='SEO Text',
        required=False,
        translate=True,
        sanitize=False,
        sanitize_style=False,
        sanitize_form=False,
        strip_style=False,
        strip_class=False,
    )
