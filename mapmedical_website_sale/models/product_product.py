from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _website_show_quick_add(self):
        self.ensure_one()
        if self.env.user.has_group("base.group_public"):
            return False
        return super()._website_show_quick_add()
