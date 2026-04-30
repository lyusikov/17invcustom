from odoo import http
from odoo.http import request

from odoo.addons.website.controllers.main import Website as WebsiteController
from odoo.addons.website.controllers import main as website_main


class Website(WebsiteController):
    def sitemap_xml_index(self, **kwargs):
        current_website = request.website
        website_main.LOC_PER_SITEMAP = current_website.sitemap_loc_per_page or 10
        return super().sitemap_xml_index(**kwargs)
