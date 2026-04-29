from odoo.tests import HttpCase, tagged

from ..controllers.website_category_snippet import WebsiteCategorySnippet


@tagged("post_install", "-at_install", "mapmedical")
class TestWebsiteCategorySnippet(HttpCase):
    def test_get_website_category_json(self):
        data = self.url_open("/shop/get_category", data="{}", headers={"Content-Type": "application/json"})
        response = data.json()["result"]
        categories = self.env["product.public.category"].sudo().search([("parent_id", "=", False)], order="name")
        expected_response = WebsiteCategorySnippet()._get_website_category_json(categories)
        self.assertEqual(response, expected_response)
