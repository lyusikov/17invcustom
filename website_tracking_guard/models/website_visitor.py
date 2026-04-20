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
            1, true, True, yes, on
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
        MVP strategy:
        - if the guard is enabled, return an empty visitor recordset
        - otherwise, keep standard Odoo behavior
        """
        if request and self._tracking_guard_is_enabled():
            _logger.debug(
                "Website visitor tracking skipped by website_tracking_guard for path=%s",
                request.httprequest.path,
            )
            return self.browse()

        return super()._get_visitor_from_request(*args, **kwargs)
``