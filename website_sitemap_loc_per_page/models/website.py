from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    sitemap_loc_per_page = fields.Integer(
        string="Sitemap URLs per File",
        default=10,
        help="Number of URLs to include in each sitemap part.",
    )
