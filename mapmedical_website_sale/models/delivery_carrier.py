from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    additional_carrier_description = fields.Text(
        translate=True, help="Description displayed only on the Website Checkout"
    )
