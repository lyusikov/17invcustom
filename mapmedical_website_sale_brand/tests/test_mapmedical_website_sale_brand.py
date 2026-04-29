from werkzeug import urls

from odoo.tests import tagged

from odoo.addons.website.tools import MockRequest

from .common import MapmedicaWebsiteSaleBrandCommon


@tagged("post_install", "-at_install", "mapmedical")
class TestMapmedicalWebsiteSaleBrand(MapmedicaWebsiteSaleBrandCommon):
    def test_01_should_show_brand_description(self):
        with MockRequest(self.env, website=self.website):
            # Test with one brand and no category - should show description
            brand_ids = [self.brand_with_descriptions.id]
            category = None
            show_description, selected_brand = self.WebsiteBrandController._should_show_brand_description(
                brand_ids, category
            )
            self.assertTrue(show_description)
            self.assertEqual(selected_brand, self.brand_with_descriptions)

            # Test with one brand and category - should NOT show description
            category = self.category
            show_description, selected_brand = self.WebsiteBrandController._should_show_brand_description(
                brand_ids, category
            )
            self.assertFalse(show_description)
            self.assertEqual(selected_brand.id, False)

            # Test with multiple brands - should NOT show description
            brand_ids = [self.brand_with_descriptions.id, self.brand_without_descriptions.id]
            category = None
            show_description, selected_brand = self.WebsiteBrandController._should_show_brand_description(
                brand_ids, category
            )
            self.assertFalse(show_description)
            self.assertEqual(selected_brand.id, False)

    def test_02_brands_page(self):
        url = urls.url_join(self.base_url(), "/brands")
        response = self.url_open(url)

        self.assertEqual(response.status_code, 200)
        # Check that brands are present in the response
        self.assertIn(b"Brand With Descriptions", response.content)
        self.assertIn(b"Brand Without Descriptions", response.content)

    def test_03_shop_page(self):
        # Test shop without brands
        url = urls.url_join(self.base_url(), "/shop")
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)

        # Test shop with one brand
        url = urls.url_join(self.base_url(), f"/shop?brands={self.brand_with_descriptions.id}")
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
