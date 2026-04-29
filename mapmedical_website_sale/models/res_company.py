from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    alternative_products = fields.Char(default="You may also be interested in...", size=200)
