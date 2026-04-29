from unittest.mock import patch

from werkzeug.datastructures import MultiDict

from odoo.tests import tagged

from odoo.addons.website.tools import MockRequest

from .common import MapmedicaWebsiteSaleBrandCommon


@tagged("post_install", "-at_install", "mapmedical")
class TestProductTemplate(MapmedicaWebsiteSaleBrandCommon):
    def test_01_get_brands_from_request(self):
        # Test with no brands parameter
        with MockRequest(self.env, website=self.website) as mock:
            mock.httprequest.args = MultiDict()
            # Clear any auto-created cache attribute
            if hasattr(mock, "_cached_brand_ids"):
                delattr(mock, "_cached_brand_ids")
            brands = self.env["product.template"].get_brands_from_request()
            self.assertEqual(brands, [])

        # Test with valid brands parameter
        with MockRequest(self.env, website=self.website) as mock:
            mock.httprequest.args = MultiDict([("brands", "1"), ("brands", "2"), ("brands", "3")])
            if hasattr(mock, "_cached_brand_ids"):
                delattr(mock, "_cached_brand_ids")
            brands = self.env["product.template"].get_brands_from_request()
            self.assertEqual(brands, [1, 2, 3])

        # Test with invalid brands parameter (mixed valid/invalid)
        with MockRequest(self.env, website=self.website) as mock:
            mock.httprequest.args = MultiDict([("brands", "1"), ("brands", "abc"), ("brands", "3")])
            if hasattr(mock, "_cached_brand_ids"):
                delattr(mock, "_cached_brand_ids")
            brands = self.env["product.template"].get_brands_from_request()
            self.assertEqual(brands, [1, 3])

        # Test caching functionality - first call
        with MockRequest(self.env, website=self.website) as mock:
            mock.httprequest.args = MultiDict([("brands", "5"), ("brands", "6")])
            if hasattr(mock, "_cached_brand_ids"):
                delattr(mock, "_cached_brand_ids")
            brands = self.env["product.template"].get_brands_from_request()
            self.assertEqual(brands, [5, 6])

            # Second call should use cache (change args but result should be same)
            mock.httprequest.args = MultiDict([("brands", "7"), ("brands", "8")])
            brands_cached = self.env["product.template"].get_brands_from_request()
            self.assertEqual(brands_cached, [5, 6])  # Should return cached value

    def test_02_search_build_domain(self):
        # Test without brands in request
        get_brands_from_request_mock_method = (
            "odoo.addons.mapmedical_website_sale_brand.models.product_template."
            "ProductTemplate.get_brands_from_request"
        )
        with patch(get_brands_from_request_mock_method, return_value=[]):
            domain_1, domain_2, domain_3 = self.env["product.template"]._search_build_domain([[]], "", [])
            # Should return original domains without brand filtering
            self.assertIsInstance(domain_1, list)
            self.assertIsInstance(domain_2, list)
            self.assertIsInstance(domain_3, list)

        # Test with brands in request
        with patch(get_brands_from_request_mock_method, return_value=[1, 2]):
            domain_1, domain_2, domain_3 = self.env["product.template"]._search_build_domain([[]], "", [])
            # Should add brand filtering to all domains
            self.assertIsInstance(domain_1, list)
            self.assertIsInstance(domain_2, list)
            self.assertIsInstance(domain_3, list)

    def test_03_get_brands_mega_menu_data(self):
        with MockRequest(self.env, website=self.website):
            result = self.env["product.template"].get_brands_mega_menu_data()

            self.assertIn("columns", result)
            self.assertIn("total_brands", result)
            self.assertIn("max_column_size", result)
            self.assertIn("brands_per_column", result)

            # Should only include published brands
            self.assertEqual(result["total_brands"], 4)
            self.assertEqual(len(result["columns"]), 4)

            # Test that columns contain the right brands
            all_brands_in_columns = []
            for column in result["columns"]:
                all_brands_in_columns.extend(column)

            brand_names = [brand.name for brand in all_brands_in_columns]
            self.assertIn(self.manufacturer_published.name, brand_names)
            self.assertIn(self.manufacturer_another_published.name, brand_names)
            self.assertNotIn(self.manufacturer_unpublished.name, brand_names)
