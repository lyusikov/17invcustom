from lxml import html
from werkzeug import urls

from odoo import Command
from odoo.http import root
from odoo.osv import expression
from odoo.tests import HttpCase, tagged
from odoo.tools import html2plaintext

from odoo.addons.base.tests.common import BaseUsersCommon
from odoo.addons.mapmedical_product.models.product_template import CUSTOMER_LEAD_TIME
from odoo.addons.website.tools import MockRequest

from ..controllers.main import (
    ADDRESS_FIELDS_TO_NOT_REQUIRED,
    BILLING,
    MODE_TO_TYPE,
    SHIPPING,
    SHOP_ADDRESSES_PAGE_URL,
    MapmedicalWebsiteSale,
    Website,
)


@tagged("post_install", "-at_install", "mapmedical")
class TestMapmedicalWebsiteSale(BaseUsersCommon, HttpCase):
    @classmethod
    def setUpClass(cls):
        super(TestMapmedicalWebsiteSale, cls).setUpClass()
        cls.website = cls.env.ref("website.default_website").with_user(cls.user_internal)
        cls.WebsiteSaleController = MapmedicalWebsiteSale()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "email": "test@example.com",
            }
        )
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.website.user_id.partner_id.id,
                "website_id": cls.website.id,
            }
        )
        cls.commercial_partner = cls.env["res.partner"].create({"name": "Commercial Partner"})
        cls.shipping_address = cls.env["res.partner"].create(
            {
                "name": "Partner 1",
                "type": "delivery",
                "parent_id": cls.commercial_partner.id,
                "commercial_partner_id": cls.commercial_partner.id,
            }
        )
        cls.billing_address = cls.env["res.partner"].create(
            {
                "name": "Partner 2",
                "type": "invoice",
                "parent_id": cls.commercial_partner.id,
                "commercial_partner_id": cls.commercial_partner.id,
            }
        )

    def set_order_in_session(self, order):
        session = self.authenticate(self.user_internal.login, self.user_internal.login)
        self.session["sale_order_id"] = order.id
        root.session_store.save(session)

    def test_01_update_client_order_ref(self):
        order = self.sale_order
        self.set_order_in_session(order)
        self.assertFalse(order.client_order_ref)

        self.make_jsonrpc_request(
            urls.url_join(self.base_url(), "/shop/update_client_order_ref"), params={"purchase_order_number": "PO12345"}
        )
        self.assertEqual(order.client_order_ref, "PO12345")

    def test_02_update_customer_notes(self):
        order = self.sale_order
        self.set_order_in_session(order)

        self.assertFalse(order.customer_notes)

        customer_notes = "Please deliver between 9am and 5pm"
        self.make_jsonrpc_request(
            urls.url_join(self.base_url(), "/shop/update_customer_notes"), params={"customer_notes": customer_notes}
        )
        cleaned_notes = html.fromstring(order.customer_notes).text_content()
        self.assertEqual(cleaned_notes, customer_notes)

    def test_03_update_default_address(self):
        order = self.sale_order
        order.partner_id = self.commercial_partner

        self.commercial_partner.default_partner_shipping_address_id = self.shipping_address.id
        self.commercial_partner.default_partner_invoicing_address_id = self.billing_address.id

        self.assertEqual(self.commercial_partner.default_partner_shipping_address_id, self.shipping_address)
        self.assertEqual(self.commercial_partner.default_partner_invoicing_address_id, self.billing_address)

        self.set_order_in_session(order)

        website = self.website.with_user(self.user_internal)
        with MockRequest(self.shipping_address.with_user(self.user_internal).env, website=website):
            kw = {"is_default_address": "on", "mode": "shipping"}
            self.WebsiteSaleController._update_default_address(
                self.commercial_partner, order, self.shipping_address.id, kw
            )
            self.assertEqual(self.commercial_partner.default_partner_shipping_address_id.id, self.shipping_address.id)
            self.assertEqual(self.commercial_partner.default_partner_invoicing_address_id.id, self.billing_address.id)

            kw.pop("is_default_address")
            self.WebsiteSaleController._update_default_address(
                self.commercial_partner, order, self.shipping_address.id, kw
            )
            self.assertFalse(self.commercial_partner.default_partner_shipping_address_id)

    def test_04_redirect_to_addresses_page(self):
        with MockRequest(self.user_internal.env, website=self.website):
            response = self.WebsiteSaleController.redirect_to_addresses_page()

            self.assertEqual(response.status_code, 303)
            self.assertIn(SHOP_ADDRESSES_PAGE_URL, response.headers["Location"])

    def test_05_get_addresses_mandatory_fields(self):
        with MockRequest(self.user_internal.env, website=self.website):
            billing_required_fields = self.WebsiteSaleController._get_mandatory_fields_billing()
            shipping_required_fields = self.WebsiteSaleController._get_mandatory_fields_shipping()
            for non_required_field in ADDRESS_FIELDS_TO_NOT_REQUIRED:
                for required_fields in [billing_required_fields, shipping_required_fields]:
                    self.assertNotIn(non_required_field, required_fields)

    def test_06_address_and_checkout_form_save(self):
        order = self.sale_order
        order.order_line = [
            Command.create(
                {
                    "product_id": self.env.ref("product.product_delivery_01").id,
                    "product_uom_qty": 1,
                    "price_unit": 50,
                }
            )
        ]
        self.set_order_in_session(order)

        base_vals = {key: "test" for key in ["name", "street", "city", "zip"]}
        vals = {
            **base_vals,
            "country_id": self.env.ref("base.us").id,
            "state_id": self.env.ref("base.state_us_1").id,
            "type": MODE_TO_TYPE[BILLING],
        }
        all_values = {**vals, "use_same": "1", "submitted": "1"}

        website = self.website.with_user(self.user_internal)
        with MockRequest(
            self.shipping_address.with_user(self.user_internal).env, website=website, sale_order_id=order.id
        ) as req:
            req.httprequest.method = "POST"
            self.WebsiteSaleController.address(**all_values, mode=BILLING)
            stored_billing_partner = billing_partner = order.partner_invoice_id
            shipping_partner = order.partner_shipping_id
            for key in vals:
                if key != "type":
                    self.assertEqual(billing_partner[key], shipping_partner[key])
            self.assertEqual(billing_partner.type, MODE_TO_TYPE[BILLING])
            self.assertEqual(shipping_partner.type, MODE_TO_TYPE[SHIPPING])

            vals["type"] = MODE_TO_TYPE[SHIPPING]
            self.WebsiteSaleController._checkout_form_save(("new", SHIPPING), vals, all_values)
            shipping_partner = order.partner_shipping_id
            self.assertEqual(shipping_partner.type, MODE_TO_TYPE[SHIPPING])

            billing_partner = order.partner_invoice_id
            self.assertEqual(billing_partner, stored_billing_partner)

    def test_07_checkout_form_validate(self):
        base_vals = {key: "test" for key in ["name", "street", "city", "zip"]}
        vals = {**base_vals, "country_id": self.env.ref("base.us").id, "state_id": self.env.ref("base.state_us_1").id}
        all_values = {**vals, "use_same": "1"}
        order = self.sale_order
        website = self.website.with_user(self.user_internal)
        with MockRequest(
            self.shipping_address.with_user(self.user_internal).env, website=website, sale_order_id=order.id
        ):
            for atype in [BILLING, SHIPPING]:
                res = self.WebsiteSaleController.checkout_form_validate(("new", atype), all_values, all_values)
                expected_value = ({}, [])  # no missed required fields
                self.assertEqual(res, expected_value)

    def test_08_checkout_values(self):
        order = self.sale_order
        website = self.website.with_user(self.user_internal)
        with MockRequest(
            self.shipping_address.with_user(self.user_internal).env, website=website, sale_order_id=order.id
        ):
            res = self.WebsiteSaleController.checkout_values(order)
            self.assertFalse(res["shippings"])
            self.assertFalse(res["billings"])
            order.partner_id = self.commercial_partner.id
            res = self.WebsiteSaleController.checkout_values(order)
            self.assertEqual(res["shippings"], self.shipping_address)
            self.assertEqual(res["billings"], self.billing_address)

    def test_09_search(self):
        WebsiteController = Website()
        manufacturer = self.env["product.manufacturer"].create({"name": "<test_manufacturer>"})
        products = self.env["product.template"].create(
            [
                {
                    "name": f"Test Searchable Product {x}",
                    "sale_ok": True,
                    "description_sale": f"<Test Description {x}>",
                    "mfr_product_code": f"<TestMFR {x}>",
                    "unique_reference": f"<TestReference {x}>",
                    "manufacturer_id": manufacturer.id,
                    "customer_lead_time": CUSTOMER_LEAD_TIME[x - 1][0],
                }
                for x in range(1, 6)
            ]
        )
        with MockRequest(self.env, website=self.website, routing=True):
            options = WebsiteController._get_hybrid_search_options()
            options["display_currency"] = self.website.currency_id

            # test searching by all variants of terms
            for search_term in ["Searchable Pr", "<TestMFR ", "<Test Description ", f"{manufacturer.name} <TestMFR "]:
                result = WebsiteController.autocomplete(term=search_term, options=options, limit=10)
                self.assertEqual(result["results_count"], len(products))
                for x in range(5):
                    expected_name = html2plaintext(result["results"][x]["name"]).replace(" ", "")
                    self.assertEqual(expected_name, f"TestSearchableProduct{x + 1}")

            # test search result page with pages
            LIMIT = 1
            options["page"] = 1
            result = WebsiteController.autocomplete(term="Test Searchable Product", options=options, limit=LIMIT)
            self.assertEqual(result["results_count"], 5)
            self.assertEqual(len(result["results"]), LIMIT)
            expected_name = html2plaintext(result["results"][0]["name"]).replace(" ", "")
            self.assertEqual(expected_name, "TestSearchableProduct1")

            # check search detail
            search_detail = self.env["product.template"]._search_get_detail(self.website, "id", options)
            self.assertEqual(
                search_detail["search_fields"],
                ["name", "mfr_product_code", "description_sale", "raw_name", "unique_reference"],
            )
            self.assertIn("customer_lead_time", search_detail["mapping"])
            self.assertIn("page", search_detail)
            self.assertEqual(
                search_detail["mapping"]["customer_lead_time"],
                {
                    "match": True,
                    "name": "customer_lead_time",
                    "type": "text",
                },
            )

            # check domains building
            search_term = "term"
            domain = self.env["product.template"]._search_build_domain([], search_term, search_detail["search_fields"])
            expected_domain = (
                [(search_detail["search_fields"][0], "=ilike", f"{search_term}%")],
                [(search_detail["search_fields"][0], "ilike", search_term)],
                expression.OR([[(field, "ilike", search_term)] for field in search_detail["search_fields"][1:]]),
            )
            self.assertEqual(domain, expected_domain)

            # test priority domain
            old_name = products[0].name
            products[0].name = f"Test {old_name}"
            result = WebsiteController.autocomplete(term="Test Searchable Product", options=options)
            self.assertEqual(result["results_count"], 5)
            expected_name_1 = html2plaintext(result["results"][0]["name"]).replace(" ", "")
            self.assertEqual(expected_name_1, "TestSearchableProduct2")
            expected_name_2 = html2plaintext(result["results"][4]["name"]).replace(" ", "")
            self.assertEqual(expected_name_2, "TestTestSearchableProduct1")
