from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sitemap_loc_per_page = fields.Integer(
        related="website_id.sitemap_loc_per_page",
        readonly=False,
        help="Number of URLs to include in each sitemap file.",
    )
