from odoo.tests import TransactionCase, tagged

from odoo.addons.mapmedical_product.models.product_template import CUSTOMER_LEAD_TIME

from ..models.product_template import THUMBNAIL_PATH


@tagged("post_install", "-at_install", "mapmedical")
class TestProductTemplate(TransactionCase):
    def test_search_render_results(self):
        product = self.env.ref("product.product_product_4_product_template")
        self.assertFalse(product.url_image)

        res = product._search_render_results(["id", "name"], {"image_url": {}}, "", 1)
        self.assertEqual(res[0]["image_url"], THUMBNAIL_PATH)

        product.url_image = "<test_url>"
        res = product._search_render_results(["id", "name"], {"image_url": {}}, "", 1)
        self.assertEqual(res[0]["image_url"], product.url_image)

        product.customer_lead_time = CUSTOMER_LEAD_TIME[0][0]
        res = product._search_render_results(["id", "name"], {"image_url": {}}, "", 1)
        self.assertEqual(res[0]["customer_lead_time"], CUSTOMER_LEAD_TIME[0][1])

    def test_compute_raw_name(self):
        product = self.env.ref("product.product_product_4_product_template")
        manufacturer = self.env["product.manufacturer"].create({"name": "<test_manufacturer>"})
        sku = "<test_sku>"
        product.update(
            {
                "manufacturer_id": manufacturer.id,
                "mfr_product_code": sku,
            }
        )

        self.assertEqual(product.raw_name, f"{manufacturer.name} {sku}")

        product.mfr_product_code = ""
        self.assertEqual(product.raw_name, manufacturer.name)

        product.update(
            {
                "manufacturer_id": False,
                "mfr_product_code": sku,
            }
        )
        self.assertEqual(product.raw_name, sku)

        product.mfr_product_code = ""
        self.assertEqual(product.raw_name, "")
