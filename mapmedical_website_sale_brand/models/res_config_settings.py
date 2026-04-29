from odoo import fields, models

from ..constants import DEFAULT_BRANDS_MENU_LIMIT, DEFAULT_BRANDS_WIDGET_LIMIT


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_brands_widget_limit = fields.Integer(
        string="Brands Widget Limit",
        default=DEFAULT_BRANDS_WIDGET_LIMIT,
        config_parameter="mapmedical_website_sale_brand.brands_widget_limit",
        help="Maximum number of brands to display in the shop page brands filter widget.",
    )

    website_brands_menu_limit = fields.Integer(
        string="Brands Menu Limit",
        default=DEFAULT_BRANDS_MENU_LIMIT,
        config_parameter="mapmedical_website_sale_brand.brands_menu_limit",
        help="Maximum number of brands to display in the header mega menu dropdown.",
    )
