from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    seo_criteria = fields.Selection(
        selection=[
            ('category', 'Category'),
            ('attributes', 'Attributes'),
            ('both', 'Both'),
        ],
        string="SEO Criteria",
        default='category',
        config_parameter='kw_seo_configuration.seo_criteria',
        help="""Choose which criteria to use for SEO rules:
                Categories, Attributes, or Both."""
    )
