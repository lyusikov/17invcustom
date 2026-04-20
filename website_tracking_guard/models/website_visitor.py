import logging

from odoo import api, models
from odoo.http import request

_logger = logging.getLogger(__name__)


class WebsiteVisitor(models.Model):
    _inherit = "website.visitor"

    @api.model
    def _tracking_guard_is_enabled(self):
        """
        System parameter:
            website_tracking_guard.disable_tracking = 1

        Accepted truthy values:
            1, true, yes, on
        """
        value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("website_tracking_guard.disable_tracking", "0")
        )
        return str(value).strip().lower() in ("1", "true", "yes", "on")

    @api.model
    def _get_visitor_from_request(self, *args, **kwargs):
        """
        If tracking is disabled, return an empty visitor recordset.
        This disables visitor tracking creation/lookup from frontend flows.
        """
        if request and self._tracking_guard_is_enabled():
            _logger.info(
                "website_tracking_guard: visitor tracking skipped for path=%s",
                request.httprequest.path,
            )
            return self.browse()

        return super()._get_visitor_from_request(*args, **kwargs)

    def _add_viewed_product(self, product_id, *args, **kwargs):
        """
        website_sale calls this method for recently viewed products.

        If tracking is disabled OR the visitor recordset is empty,
        do nothing instead of crashing on ensure_one().
        """
        if not self:
            _logger.debug(
                "website_tracking_guard: skip _add_viewed_product because visitor is empty"
            )
            return False

        if self._tracking_guard_is_enabled():
            _logger.debug(
                "website_tracking_guard: skip _add_viewed_product because tracking is disabled"
            )
            return False

        return super()._add_viewed_product(product_id, *args, **kwargs)