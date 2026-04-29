from odoo import _, api, fields, models

from ..constants import SLUG_UNSAFE_RE


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    custom_url = fields.Char(compute="_compute_custom_url", store=True, readonly=False)

    @api.depends("name", "parent_id")
    def _compute_custom_url(self):
        for rec in self:
            if rec.name:
                url = SLUG_UNSAFE_RE.sub("", rec.name).replace(" ", "-").replace("/", "").lower()
                if rec.parent_id:
                    url = f"{rec.parent_id.custom_url}/{url}"
                rec.custom_url = url
