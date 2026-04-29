from odoo import _, fields, models

from ..constants import DEFAULT_LOC_PER_PAGE


class Website(models.Model):
    _inherit = "website"

    sitemap_loc_per_page = fields.Integer(
        string="Sitemap URLs per File",
        default=DEFAULT_LOC_PER_PAGE,
        help="Number of URLs to include in each sitemap part.",
    )

    def _prepare_sale_order_values(self, partner_sudo):
        values = super()._prepare_sale_order_values(partner_sudo)
        values["partner_shipping_id"] = partner_sudo.default_partner_shipping_address_id.id or partner_sudo.id
        values["partner_invoice_id"] = partner_sudo.default_partner_invoicing_address_id.id or partner_sudo.id
        return values

    def _search_with_fuzzy(self, search_type, search, limit, order, options):
        """
        Disable fuzzy search globally
        """
        options["allowFuzzy"] = False
        return super()._search_with_fuzzy(search_type, search, limit, order, options)

    @staticmethod
    def _get_product_sort_mapping():
        sort_mapping = [
            ("website_sequence asc", _("Featured")),
            ("create_date desc", _("Newest Arrivals")),
            ("name asc", _("Name (A-Z)")),
            ("list_price asc", _("Price - Low to High")),
            ("list_price desc", _("Price - High to Low")),
            ("manufacturer_id asc", _("Brand")),
        ]
        return sort_mapping
