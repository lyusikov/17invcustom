from odoo import api, fields, models


class ProductManufacturer(models.Model):
    _inherit = "product.manufacturer"
    _order = "sequence, name, id"

    is_published = fields.Boolean(
        string="Published on Website",
        default=False,
        index=True,
        help="If checked, this brand will be available for filtering on the website shop page.",
    )
    description_top = fields.Html(
        string="Top Description",
        translate=True,
        sanitize_attributes=False,
    )
    description_bottom = fields.Html(
        string="Bottom Description",
        translate=True,
        sanitize_attributes=False,
    )
    website_url = fields.Char(compute="_compute_website_url", store=True, readonly=False)
    seo_title = fields.Char()
    seo_description = fields.Text()
    seo_header = fields.Char()
    sequence = fields.Integer(index=True, default=10000)

    @api.depends("name")
    def _compute_website_url(self):
        for rec in self:
            if rec.name:
                url = rec.name.replace(" ", "-")
                rec.website_url = f"{url}"

    def lower_website_url(self):
        for rec in self:
            rec.website_url = rec.website_url.lower()

    @api.model
    def get_published_brands(self, limit=None, order="name", additional_domain=None):
        """
        Get published brands with optional filtering.

        Args:
            limit (int, optional): Maximum number of brands to return
            order (str): Order by clause (default: "name")
            additional_domain (list, optional): Additional domain conditions

        Returns:
            recordset: Published brands matching the criteria
        """
        domain = [("is_published", "=", True)]

        if additional_domain:
            domain.extend(additional_domain)

        return self.sudo().search(domain, order=order, limit=limit)

    @api.model
    def get_all_brands(self, limit=None, order="name", additional_domain=None):
        """
        Get all brands (published and unpublished) with optional filtering.

        Args:
            limit (int, optional): Maximum number of brands to return
            order (str): Order by clause (default: "name")
            additional_domain (list, optional): Additional domain conditions

        Returns:
            recordset: All brands matching the criteria
        """
        domain = additional_domain or []
        return self.sudo().search(domain, order=order, limit=limit)
