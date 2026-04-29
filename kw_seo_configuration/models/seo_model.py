from odoo import models, fields


class SEOModel(models.Model):
    _name = 'seo.model'
    _description = 'SEO Model'

    seo_title = fields.Char(string="SEO Title", translate=True)
    seo_description = fields.Text(
        string="SEO Description",
        translate=True
    )
    seo_header = fields.Char(
        string="SEO Header",
        required=False,
        translate=True
    )
    seo_text = fields.Html(
        string="SEO Text",
        required=False,
        translate=True,
        sanitize=False,
        sanitize_style=False,
        sanitize_form=False,
        strip_style=False,
        strip_class=False,
    )

    related_categories_ids = fields.Many2many(
        comodel_name='product.public.category',
        string="Related Categories",
        help="Select the categories related to this SEO configuration."
    )

    attr_values_ids = fields.Many2many(
        comodel_name='product.attribute.value',
        string="Attribute Values",
        help="Select the attribute values related to this SEO configuration."
    )

    apply_all_products_page = fields.Boolean(
        string="Apply to All Products Page",
        default=False,
        help="This SEO configuration is applied to the All Products page."
    )

    website_ids = fields.Many2many(
        comodel_name='website',
        string="Websites",
        help="Select the websites this SEO rule applies to."
    )
