from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    alternative_products = fields.Char(
        related="company_id.alternative_products",
        readonly=False,
    )
    sitemap_loc_per_page = fields.Integer(
        related="website_id.sitemap_loc_per_page",
        readonly=False,
        help="Number of URLs to include in each sitemap part",
    )
