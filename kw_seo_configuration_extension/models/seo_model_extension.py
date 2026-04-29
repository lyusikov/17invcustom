# -*- coding: utf-8 -*-

from odoo import fields, models


class SEOModelExtension(models.Model):
    _inherit = 'seo.model'

    name = fields.Char(
        string='Name',
        required=True,
        help='The internal name of the SEO configuration.'
    )
    seo_keywords = fields.Char(
        string='SEO Keywords',
        help='Comma-separated keywords for search engines.'
    )
    product_tag_ids = fields.Many2many(
        comodel_name='product.tag',
        string='Product Tags',
        help='Related product tags for this SEO configuration.'
    )
    related_products_count = fields.Integer(
        string='Related Products',
        compute='_compute_related_products_count',
        store=True,
    )

    def _compute_related_products_count(self):
        for record in self:
            product_tags = record.product_tag_ids
            if product_tags:
                record.related_products_count = self.env['product.template'].search_count([
                    ('tag_ids', 'in', product_tags.ids)
                ])
            else:
                record.related_products_count = 0
