import base64
import datetime
from hashlib import md5
from itertools import islice

from odoo import fields, http
from odoo.http import request

from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.website.controllers.main import SITEMAP_CACHE_TIME, QueryURL, Website
from odoo.addons.website_sale.controllers.main import WebsiteSale

from ..constants import DEFAULT_LOC_PER_PAGE

SHOP_ADDRESSES_PAGE_URL = "/shop/checkout"
IS_CHECKED = "on"
BILLING = "billing"
SHIPPING = "shipping"
MODE_TO_TYPE = {BILLING: "invoice", SHIPPING: "delivery"}
ADDRESS_FIELDS_TO_NOT_REQUIRED = ["email", "phone"]

AUTOCOMPLETE_SEARCH_PRODUCTS_ONLY = "products_only"


class Website(Website):
    @http.route("/website/snippet/filters", type="json", auth="public", website=True)
    def get_dynamic_filter(
        self, filter_id, template_key, limit=None, search_domain=None, with_sample=False, productTemplateId=None
    ):
        """
        Override to accept productTemplateId parameter sent from website_sale JS.
        The parameter is accepted but not used - it's only needed to prevent warning.
        """
        return super().get_dynamic_filter(
            filter_id=filter_id,
            template_key=template_key,
            limit=limit,
            search_domain=search_domain,
            with_sample=with_sample,
        )

    @http.route("/sitemap.xml", type="http", auth="public", website=True, multilang=False, sitemap=False)
    def sitemap_xml_index(self, **kwargs):
        """Method is OVERRIDEN to set up the number of URLs to include in each sitemap part"""
        current_website = request.website
        Attachment = request.env["ir.attachment"].sudo()
        View = request.env["ir.ui.view"].sudo()
        mimetype = "application/xml;charset=utf-8"
        content = None
        url_root = request.httprequest.url_root
        # For a same website, each domain has its own sitemap (cache)
        hashed_url_root = md5(url_root.encode()).hexdigest()[:8]
        sitemap_base_url = "/sitemap-%d-%s" % (current_website.id, hashed_url_root)

        def create_sitemap(url, content):
            return Attachment.create(
                {
                    "raw": content.encode(),
                    "mimetype": mimetype,
                    "type": "binary",
                    "name": url,
                    "url": url,
                }
            )

        dom = [("url", "=", "%s.xml" % sitemap_base_url), ("type", "=", "binary")]
        sitemap = Attachment.search(dom, limit=1)
        if sitemap:
            # Check if stored version is still valid
            create_date = fields.Datetime.from_string(sitemap.create_date)
            delta = datetime.datetime.now() - create_date
            if delta < SITEMAP_CACHE_TIME:
                content = base64.b64decode(sitemap.datas)

        if not content:
            # Remove all sitemaps in ir.attachments as we're going to regenerated them
            dom = [
                ("type", "=", "binary"),
                "|",
                ("url", "=like", "%s-%%.xml" % sitemap_base_url),
                ("url", "=", "%s.xml" % sitemap_base_url),
            ]
            sitemaps = Attachment.search(dom)
            sitemaps.unlink()

            # Itransition changes start
            # Get sitemap URLs per page from website settings
            loc_per_page = current_website.sitemap_loc_per_page or DEFAULT_LOC_PER_PAGE
            pages = 0
            locs = request.website.with_user(request.website.user_id)._enumerate_pages()
            while True:
                values = {
                    "locs": islice(locs, 0, loc_per_page),
                    "url_root": url_root[:-1],
                }
                # Itransition changes end

                urls = View._render_template("website.sitemap_locs", values)
                if urls.strip():
                    content = View._render_template("website.sitemap_xml", {"content": urls})
                    pages += 1
                    last_sitemap = create_sitemap("%s-%d.xml" % (sitemap_base_url, pages), content)
                else:
                    break

            if not pages:
                return request.not_found()
            elif pages == 1:
                # rename the -id-page.xml => -id.xml
                last_sitemap.write(
                    {
                        "url": "%s.xml" % sitemap_base_url,
                        "name": "%s.xml" % sitemap_base_url,
                    }
                )
            else:
                pages_with_website = [
                    "%d-%s-%d" % (current_website.id, hashed_url_root, p) for p in range(1, pages + 1)
                ]

                # Sitemaps must be split in several smaller files with a sitemap index
                content = View._render_template(
                    "website.sitemap_index_xml",
                    {
                        "pages": pages_with_website,
                        # URLs inside the sitemap index have to be on the same
                        # domain as the sitemap index itself
                        "url_root": url_root,
                    },
                )
                create_sitemap("%s.xml" % sitemap_base_url, content)

        return request.make_response(content, [("Content-Type", mimetype)])

    @http.route("/website/snippet/autocomplete", type="json", auth="public", website=True)
    def autocomplete(self, search_type=None, term=None, order=None, limit=5, max_nb_chars=999, options=None):
        """
        Override method to change search type to `products_only`
        """
        return super().autocomplete(
            search_type=AUTOCOMPLETE_SEARCH_PRODUCTS_ONLY,  # use `products_only` search type
            term=term,
            order=order,
            limit=limit,
            max_nb_chars=max_nb_chars,
            options=options,
        )

    @http.route(
        [
            "/website/search",
            "/website/search/page/<int:page>",
            "/website/search/<string:search_type>",
            "/website/search/<string:search_type>/page/<int:page>",
        ],
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def hybrid_list(self, page=1, search="", search_type="all", **kw):
        """
        Override method to add paginator page number into search to fix perfomance
        and change search type to `products_only` and exclude limit
        """
        if not search:
            return request.render("website.list_hybrid")
        options = self._get_hybrid_search_options(**kw)
        # Itransition changes start
        options["page"] = page  # add page number into options to save it for future operations
        data = self.autocomplete(
            search_type=AUTOCOMPLETE_SEARCH_PRODUCTS_ONLY,  # use `products_only` search type
            term=search,
            order="name asc",
            limit=500,
            max_nb_chars=200,
            options=options,
        )
        # Itransition changes end
        results = data.get("results", [])
        # Itransition changes start
        search_count = data.get("results_count")  # get new count of results
        # Itransition changes end
        parts = data.get("parts", {})

        step = 50
        pager = portal_pager(
            url="/website/search/%s" % search_type,
            url_args={"search": search},
            total=search_count,
            page=page,
            step=step,
        )
        ProductCategory = request.env["product.public.category"]
        keep = QueryURL(
            "/shop",
            {
                "search": search,
            },
        )
        values = {
            "pager": pager,
            "results": results,
            "parts": parts,
            "search": search,
            "fuzzy_search": data.get("fuzzy_search"),
            "search_count": search_count,
            "category": ProductCategory,
            "categories": ProductCategory.search([("parent_id", "=", False)]),
            "keep": keep,
        }
        return request.render("website.list_hybrid", values)


class MapmedicalWebsiteSale(WebsiteSale):
    @http.route(["/shop/update_client_order_ref"], type="json", methods=["POST"], auth="public", website=True)
    def update_client_order_ref(self, purchase_order_number=None):
        """
        Update the client order reference for the current sale order.
        :type purchase_order_number: str, optional
        """
        order = request.website.sale_get_order()
        if order:
            order.sudo().update({"client_order_ref": purchase_order_number})

    @http.route(["/shop/update_customer_notes"], type="json", methods=["POST"], auth="public", website=True)
    def update_customer_notes(self, customer_notes=None):
        """
        Update the customer notes for the current sale order.
        :type customer_notes: str, optional
        """
        order = request.website.sale_get_order()
        if order:
            order.sudo().update({"customer_notes": customer_notes})

    def _update_default_address(self, partner, order, address_partner_id, kw):
        """
        Update the default address status for a partner based on the form input.

        :param partner: res.partner object being updated.
        :param address_partner_id: int identifier of the billing/shipping partner.
        :param kw: dict containing form data, including the "is_default_address" flag.
        :param order: sale.order object associated with the partner.
        """
        address_partner = request.env["res.partner"].sudo().browse(address_partner_id)
        is_default_address = kw.get("is_default_address") == IS_CHECKED

        mode_to_field = {
            BILLING: "default_partner_invoicing_address_id",
            SHIPPING: "default_partner_shipping_address_id",
        }

        mode = kw.get("mode")
        if mode in mode_to_field:
            if is_default_address:
                setattr(partner, mode_to_field[mode], address_partner.id)
            elif partner[mode_to_field[mode]] == address_partner:
                setattr(partner, mode_to_field[mode], False)

    def _get_order_address_ids(self, order):
        return order.partner_shipping_id.id, order.partner_invoice_id.id

    def _get_same_shipping_address_domain(self, parent_partner, name, min_id):
        return [
            ("id", "child_of", parent_partner),
            ("type", "=", "delivery"),
            ("name", "=", name),
            ("id", ">", min_id),
        ]

    @http.route(["/shop/address"], type="http", methods=["GET", "POST"], auth="public", website=True, sitemap=False)
    def address(self, **kw):
        """Extend method (controller) to override addresses postcreation logic and
        handle the address request and update the default address for a partner.
        """
        order = request.website.sale_get_order()
        partner = order.partner_id
        # save the current billing and shipping addresses
        pre_shipping_address_id, pre_billing_address_id = self._get_order_address_ids(order)
        is_submit = request.httprequest.method == "POST" and "submitted" in kw

        response = super().address(**kw)

        post_shipping_address_id, post_billing_address_id = self._get_order_address_ids(order)
        mode = kw.get("mode")
        if mode == BILLING and pre_billing_address_id != post_billing_address_id:
            # case when new billing address has been created
            address_partner_id = post_billing_address_id
            # additional case if shipping will be the same as billing (use_same param)
            if kw.get("use_same"):
                # the same billing address has been created via overriding `_checkout_form_save` method in this file
                domain = self._get_same_shipping_address_domain(
                    partner.commercial_partner_id.ids, kw.get("name"), address_partner_id
                )
                the_same_shipping = request.env["res.partner"].sudo().search(domain, order="id desc", limit=1)
                if the_same_shipping:
                    # if it exists when need to cleanup old defaults for billing addresses
                    order.partner_shipping_id = the_same_shipping.id
                    self._update_default_address(partner, order, the_same_shipping.id, {**kw, "mode": SHIPPING})
        elif mode == SHIPPING and pre_shipping_address_id != post_shipping_address_id:
            # case when new shipping address has been created
            address_partner_id = post_shipping_address_id
        else:
            # case when existing partner has been changed/ no address
            address_partner_id = int(kw.get("partner_id", -1))

        if address_partner_id > 0 and is_submit:
            self._update_default_address(partner, order, address_partner_id, kw)
        return response

    @staticmethod
    def redirect_to_addresses_page():
        """Redirect to the shop checkout page."""
        return request.redirect(SHOP_ADDRESSES_PAGE_URL)

    def checkout_form_validate(self, mode, all_form_values, data):
        # new address validation: remove "email" and "phone" from required fields for new address
        error, error_message = super().checkout_form_validate(mode, all_form_values, data)
        _, address_mode = mode
        shipping_the_same = all_form_values.get("use_same", False)
        if address_mode == BILLING and not shipping_the_same:
            error.pop("email", False)
        if address_mode == SHIPPING or (address_mode == BILLING and shipping_the_same):
            error.pop("phone", False)

        # if after cleanup no missing fields then need to remove 'required fields' msg
        missing_msg = "Some required fields are empty."
        if missing_msg in error_message:
            missing_required_fields = [err for err in error.values() if err == "missing"]
            if not missing_required_fields:
                error_message.remove(missing_msg)
        return error, error_message

    @http.route(["/shop/checkout"], type="http", auth="public", website=True, sitemap=False)
    def checkout(self, **post):
        """
        Override the checkout method to remove the page auto-skipping of step 2 - Shipping.
        """
        order_sudo = request.website.sale_get_order()
        request.session["sale_last_order_id"] = order_sudo.id
        redirection = self.checkout_redirection(order_sudo)
        if redirection:
            return redirection
        if order_sudo._is_public_order():
            return request.redirect("/shop/address")

        redirection = self.checkout_check_address(order_sudo)
        if redirection:
            return redirection

        if post.get("express"):
            # Itransition changes start
            return self.redirect_to_addresses_page()
            # Itransition changes end

        values = self.checkout_values(order_sudo, **post)
        # Avoid useless rendering if called in ajax
        if post.get("xhr"):
            return "ok"
        return request.render("website_sale.checkout", values)

    def checkout_values(self, order, **kw):
        def _get_partners(order, mode):
            commercial_partner = order.partner_id.commercial_partner_id
            Partner = order.partner_id.with_context(show_address=1).sudo()
            return Partner.search(
                [("id", "child_of", commercial_partner.ids), ("type", "=", MODE_TO_TYPE[mode])], order="id desc"
            )

        res = super().checkout_values(order, **kw)
        order = res["order"]
        res["billings"] = _get_partners(order, BILLING)
        res["shippings"] = _get_partners(order, SHIPPING)
        return res

    def _cleanup_address_mandatory_fields(self, fields):
        # redirect checking process: remove "email" and "phone" from required fields for new address
        for field in ADDRESS_FIELDS_TO_NOT_REQUIRED:
            if field in fields:
                fields.remove(field)
        return fields

    def _get_mandatory_fields_billing(self, country_id=False):
        """Extend getting billing requried fields - remove needed fields"""
        return self._cleanup_address_mandatory_fields(super()._get_mandatory_fields_billing(country_id=country_id))

    def _get_mandatory_fields_shipping(self, country_id=False):
        """Extend getting shipping requried fields - remove needed fields"""
        return self._cleanup_address_mandatory_fields(super()._get_mandatory_fields_shipping(country_id=country_id))

    def _checkout_form_save(self, mode, checkout, all_values):
        """Extend method to create invoice and billing addresses instead of other for use_same attribute"""
        if mode == ("new", BILLING) and all_values.get("use_same"):
            # for case when new billing address will be created with use_same parameter
            # the OOTB "other" address creation will be replaced with "invoice" + "delivery"
            # creation and these addresses will be the same
            new_billing_address = super()._checkout_form_save(
                mode, {**checkout, "type": MODE_TO_TYPE[BILLING]}, all_values
            )
            super()._checkout_form_save(mode, {**checkout, "type": MODE_TO_TYPE[SHIPPING]}, all_values)
            # return only billing address id for OOTB compatibility
            return new_billing_address
        else:
            # OOTB Logic
            return super()._checkout_form_save(mode, checkout, all_values)

    @http.route()
    def cart(self, access_token=None, revive="", **post):
        if request.env.user == request.env.ref("base.public_user"):
            return request.redirect("/shop")
        return super().cart(access_token=access_token, revive=revive, **post)

    def _get_cart_notification_information(self, order, line_ids):
        """Method extended to replace image_url with product's image_128."""
        res = super()._get_cart_notification_information(order, line_ids)
        if res and "lines" in res:
            lines = order.order_line.filtered(lambda line: line.id in line_ids)
            lines_by_id = {line.id: line for line in lines}

            for line_data in res["lines"]:
                line_id = line_data.get("id")
                if line_id in lines_by_id and lines_by_id[line_id].product_id.url_image:
                    line_data["image_url"] = lines_by_id[line_id].product_id.url_image
        return res

    def _prepare_product_values(self, product, category, search, **kwargs):
        values = super()._prepare_product_values(product, category, search, **kwargs)
        values["current_category"] = product.public_categ_ids[:1]
        values["category_depth"] = 0
        if not values["category"] and product.public_categ_ids:
            values["category"] = product.public_categ_ids[:1]
            if values["category"].parent_path:
                values["category_depth"] = values["category"].parent_path.count("/")
        return values
