from odoo import fields, models


class ProductBrandCategorySequence(models.Model):
    _name = "product.brand.category.sequence"
    _description = "Product Sequences"
    _order = "sequence, id"

    manufacturer_id = fields.Many2one("product.manufacturer", "Brand", index=True)
    sequence = fields.Integer(index=True, default=10000)
    product_tmpl_id = fields.Many2one("product.template", "Product")
    public_categ_id = fields.Many2one("product.public.category", "Product Category")

    _sql_constraints = [
        (
            "unique_account_by_transfer_model",
            "UNIQUE(product_tmpl_id, public_categ_id)",
            "Only one account occurrence by transfer model",
        )
    ]
