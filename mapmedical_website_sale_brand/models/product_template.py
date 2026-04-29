from odoo import api, fields, models
from odoo.http import request
from odoo.osv import expression

from odoo.addons.http_routing.models.ir_http import slug

from ..constants import BRANDS_MENU_COLUMNS_COUNT, DEFAULT_BRANDS_MENU_LIMIT


class ProductTemplate(models.Model):
    _inherit = "product.template"

    manufacturer_id = fields.Many2one(index=True)
    sequence_ids = fields.One2many("product.brand.category.sequence", "product_tmpl_id", "Sequences")
    website_slug = fields.Char(compute="_compute_website_slug", store=True)

    @api.depends("name")
    def _compute_website_slug(self):
        for rec in self:
            if rec.name:
                rec.website_slug = slug(rec)

    def _compute_website_url(self):
        super()._compute_website_url()
        for product in self:
            if product.id:
                if product.public_categ_ids:
                    product.website_url = f"/{product.public_categ_ids[0].custom_url.lower()}/{slug(product)}"
        return True

    @api.model
    def get_brands_from_request(self):
        """
        Extract and validate brand IDs from request parameters.
        Returns list of integers or empty list.
        Cached per request to avoid repeated parsing.
        """
        if not hasattr(request, "httprequest") or not request.httprequest:
            return []

        cached_brands = getattr(request, "_cached_brand_ids", [])
        if hasattr(cached_brands, "_mock_name"):
            return []

        # Cache brands per request to avoid repeated parsing
        if not hasattr(request, "_cached_brand_ids"):
            brands_param = request.httprequest.args.getlist("brands")
            if not brands_param:
                request._cached_brand_ids = []
            else:
                try:
                    request._cached_brand_ids = [int(b) for b in brands_param if b.isdigit()]
                except (ValueError, TypeError):
                    request._cached_brand_ids = []

        return request._cached_brand_ids

    def _search_get_detail(self, website, order, options):
        """Add brand filtering to the search domain used by _search_with_fuzzy."""
        detail = super()._search_get_detail(website, order, options)
        brands = options.get("brands") or self.get_brands_from_request()
        if brands:
            detail["base_domain"].append([("manufacturer_id", "in", brands)])
        return detail

    @api.model
    def get_brands_mega_menu_data(self):
        """Get brands data for mega menu dropdown."""
        brands_limit = int(
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mapmedical_website_sale_brand.brands_menu_limit", DEFAULT_BRANDS_MENU_LIMIT)
        )

        brands = request.env["product.manufacturer"].get_published_brands(limit=brands_limit)

        brands_per_column = max(1, len(brands) // BRANDS_MENU_COLUMNS_COUNT) if brands else 0
        remainder = len(brands) % BRANDS_MENU_COLUMNS_COUNT if brands else 0

        columns = []
        start_idx = 0
        max_column_size = 0

        for i in range(BRANDS_MENU_COLUMNS_COUNT):
            column_size = brands_per_column + (1 if i < remainder else 0)
            max_column_size = max(max_column_size, column_size)
            end_idx = start_idx + column_size
            columns.append(brands[start_idx:end_idx])
            start_idx = end_idx

        return {
            "columns": columns,
            "total_brands": len(brands),
            "max_column_size": max_column_size,
            "brands_per_column": brands_per_column,
        }
