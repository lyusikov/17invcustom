from odoo.tests import HttpCase

from ..controllers.main import WebsiteBrand


class MapmedicaWebsiteSaleBrandCommon(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.website = cls.env["website"].get_current_website()
        cls.WebsiteBrandController = WebsiteBrand()
        cls.manufacturer_published = cls.env["product.manufacturer"].create(
            {
                "name": "Published Brand",
                "is_published": True,
            }
        )
        cls.manufacturer_unpublished = cls.env["product.manufacturer"].create(
            {
                "name": "Unpublished Brand",
                "is_published": False,
            }
        )
        cls.manufacturer_another_published = cls.env["product.manufacturer"].create(
            {
                "name": "Another Published Brand",
                "is_published": True,
            }
        )
        cls.brand_with_descriptions = cls.env["product.manufacturer"].create(
            {
                "name": "Brand With Descriptions",
                "is_published": True,
                "description_top": "<p>Top description content</p>",
                "description_bottom": "<p>Bottom description content</p>",
            }
        )
        cls.brand_without_descriptions = cls.env["product.manufacturer"].create(
            {
                "name": "Brand Without Descriptions",
                "is_published": True,
            }
        )
        cls.category = cls.env["product.public.category"].create({"name": "Test Category"})
        cls.product_brand_1 = cls.env["product.template"].create(
            {
                "name": "Product Brand 1",
                "manufacturer_id": cls.brand_with_descriptions.id,
                "is_published": True,
                "website_published": True,
            }
        )
        cls.product_brand_2 = cls.env["product.template"].create(
            {
                "name": "Product Brand 2",
                "manufacturer_id": cls.brand_without_descriptions.id,
                "is_published": True,
                "website_published": True,
            }
        )
