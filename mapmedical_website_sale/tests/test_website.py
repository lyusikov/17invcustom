from odoo.tests import tagged

from odoo.addons.base.tests.common import HttpCaseWithUserPortal
from odoo.addons.mapmedical_product.models.constants import CUSTOMER_LEAD_TIME
from odoo.addons.website.tools import MockRequest


@tagged("post_install", "-at_install", "mapmedical")
class TestWebsite(HttpCaseWithUserPortal):
    def test_01_prepare_sale_order_values(self):
        partner = self.env.ref("base.res_partner_1")
        partner_shipping = self.env.ref("base.res_partner_2")
        partner_invoicing = self.env.ref("base.res_partner_3")
        website = self.env["website"].get_current_website()

        with MockRequest(self.env, website=website) as mock:
            mock.httprequest.args = {}
            res = website._prepare_sale_order_values(partner)
            self.assertEqual(res["partner_invoice_id"], partner.id)
            self.assertEqual(res["partner_shipping_id"], partner.id)

            partner.default_partner_shipping_address_id = partner_shipping.id
            partner.default_partner_invoicing_address_id = partner_invoicing.id

            res = website._prepare_sale_order_values(partner)
            self.assertEqual(res["partner_invoice_id"], partner_invoicing.id)
            self.assertEqual(res["partner_shipping_id"], partner_shipping.id)

    def test_02_customer_lead_time_data_on_website(self):
        self.env.ref("sale_product_configurator.product_product_1_product_template").customer_lead_time = (
            CUSTOMER_LEAD_TIME[0][0]
        )
        self.start_tour("/", "website_tour_add_dynamic_filter_template_product", login="admin")
        self.start_tour("/", "website_tour_check_customer_lead_time_in_website_for_logged_in_user", login="admin")
        self.start_tour("/", "website_tour_check_customer_lead_time_in_website_for_not_logged_in_user")

    def test_03_website_categories_snippet_dom(self):
        self.start_tour("/", "website_tour_add_left_side_categories_bar", login="admin")
        self.start_tour("/", "website_tour_check_categories_snippet_dom")

    def test_04_check_empty_url_image_on_website(self):
        self.env.ref("sale_product_configurator.product_product_1_product_template").url_image = ""
        self.start_tour("/", "website_tour_check_empty_url_image_in_website")

    def test_05_check_website_category_uri_param_for_breadcrumbs(self):
        self.start_tour("/", "website_tour_check_removing_caregory_param_for_breadcrumbs")

    def test_06_check_website_product_page_customizations(self):
        self.env.ref("product.product_product_4_product_template").unique_reference = "<test_unique_reference>!"
        self.start_tour("/", "website_tour_check_product_page_customizations")

    def test_07_check_website_header_customizations(self):
        self.start_tour("/", "website_tour_check_website_header_customizations_for_not_logged_in_user")
        self.start_tour("/", "website_tour_apply_header_template_menu_sales_2", login="admin")
        self.start_tour("/", "website_tour_check_website_header_customizations_for_logged_in_user", login="admin")
