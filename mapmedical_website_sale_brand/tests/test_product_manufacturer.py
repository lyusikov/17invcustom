from odoo.tests import tagged

from .common import MapmedicaWebsiteSaleBrandCommon


@tagged("post_install", "-at_install", "mapmedical")
class TestProductManufacturer(MapmedicaWebsiteSaleBrandCommon):
    def test_01_get_published_brands(self):
        published_brands = self.env["product.manufacturer"].get_published_brands()
        self.assertIn(self.manufacturer_published, published_brands)
        self.assertIn(self.manufacturer_another_published, published_brands)
        self.assertNotIn(self.manufacturer_unpublished, published_brands)

        # Test with additional domain
        additional_domain = [("name", "ilike", "Another")]
        published_brands_filtered = self.env["product.manufacturer"].get_published_brands(
            additional_domain=additional_domain
        )
        self.assertEqual(len(published_brands_filtered), 1)
        self.assertEqual(published_brands_filtered, self.manufacturer_another_published)

    def test_02_get_all_brands(self):
        all_brands = self.env["product.manufacturer"].get_all_brands()
        self.assertIn(self.manufacturer_published, all_brands)
        self.assertIn(self.manufacturer_unpublished, all_brands)
        self.assertIn(self.manufacturer_another_published, all_brands)

        # Test with additional domain
        additional_domain = [("is_published", "=", True)]
        all_brands_filtered = self.env["product.manufacturer"].get_all_brands(additional_domain=additional_domain)
        for brand in all_brands_filtered:
            self.assertTrue(brand.is_published)
        self.assertNotIn(self.manufacturer_unpublished, all_brands_filtered)
