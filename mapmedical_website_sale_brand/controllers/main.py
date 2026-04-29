from collections import defaultdict
from datetime import datetime
from types import SimpleNamespace

from markupsafe import Markup
from werkzeug.exceptions import NotFound

from odoo import api, fields, http, models, tools
from odoo.http import request
from odoo.osv import expression
from odoo.tools import config, lazy

from odoo.addons.http_routing.models.ir_http import slug, unslug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import TableCompute, WebsiteSale

from ..constants import DEFAULT_BRANDS_WIDGET_LIMIT, SLUG_UNSAFE_RE


def _prerender_categories_html(categories, category, brand, keep_fn, radio_prefix=""):
    """Pre-render the category sidebar in Python instead of QWeb.

    Replaces ~400 recursive t-call invocations for 193 categories with a
    single Python function call.  Produces identical HTML to the
    ``website_sale.option_collapse_categories_recursive`` QWeb template.
    """

    def _esc(text):
        return str(Markup.escape(text)) if text else ""

    selected_id = category.id if category else 0

    # Build {parent_id: [child, ...]} map from ORM recordsets
    children_map = {}
    for c in categories:
        pid = c.parent_id.id if c.parent_id else None
        children_map.setdefault(pid, []).append(c)

    def _render_category(cat, parent_id_str):
        children = children_map.get(cat.id, [])
        custom_url = SLUG_UNSAFE_RE.sub("", cat.custom_url or slug(cat))
        cat_url = _esc(keep_fn("/" + custom_url.lower() + "-" + str(cat.id), category=0))
        cat_name = _esc(cat.name)
        cat_id = cat.id
        radio_name = f"wsale_categories_radios_{radio_prefix}{parent_id_str}"
        checked = ' checked="checked"' if cat_id == selected_id else ""

        link_html = (
            f'<a class="form-check d-inline-block ps-4" href="{cat_url}" data-link-href="{cat_url}">'
            f'<input type="radio" class="form-check-input pe-none" name="{_esc(radio_name)}" '
            f'id="{cat_id}" value="{cat_id}"{checked}/>'
            f'<label class="form-check-label fw-normal" style="color: var(--body-color)" '
            f'for="{cat_id}">{cat_name}</label></a>'
        )

        if children:
            child_html = []
            for child in children:
                child_html.append(_render_category(child, str(cat_id) if not radio_prefix else radio_prefix))
            acc_id = f"o_wsale_cat_accordion_{radio_prefix}{cat_id}"
            return (
                f'<li class="nav-item">'
                f'<div class="accordion-header d-flex mb-1">{link_html}'
                f'<button data-bs-toggle="collapse" type="button" id="{acc_id}_title" '
                f'class="accordion-button p-0 ms-3 collapsed w-auto flex-grow-1 bg-transparent shadow-none" '
                f'data-bs-target="#{acc_id}" aria-expanded="false" aria-controls="{acc_id}"/>'
                f"</div>"
                f'<ul id="{acc_id}" class="accordion-collapse list-unstyled ps-2 pb-2 collapse" '
                f'aria-labelledby="{acc_id}_title">{"".join(child_html)}</ul></li>'
            )
        else:
            return (
                f'<li class="nav-item mb-1">'
                f'<div class="d-flex flex-wrap justify-content-between align-items-center">'
                f"{link_html}</div></li>"
            )

    parts = []
    roots = children_map.get(None, [])
    for root in roots:
        parts.append(_render_category(root, ""))

    return Markup("".join(parts))


class WebsiteBrand(WebsiteSale):
    @http.route(["/brands"], type="http", auth="public", website=True, sitemap=True)
    def brands(self):
        # Use raw SQL to fetch only name+url for 3649 brands,
        # avoiding ORM overhead (browse, field compute, access checks).
        http.request.env.cr.execute("SELECT name, website_url FROM product_manufacturer ORDER BY name")
        brands_rows = http.request.env.cr.fetchall()

        brands_by_letter = defaultdict(list)

        for name, website_url in brands_rows:
            if not name:
                continue
            first_char = name[0].upper()
            # SimpleNamespace for QWeb attribute access (brand.name, brand.website_url)
            # plus dict-style "url" key for _render_brands_html().
            entry = SimpleNamespace(name=name, url=website_url, website_url=website_url)
            if "A" <= first_char <= "Z":
                brands_by_letter[first_char].append(entry)
            else:
                brands_by_letter["other"].append(entry)

        # Sort keys: first "other", then Latin letters A-Z
        sorted_letters = []
        if "other" in brands_by_letter:
            sorted_letters.append("other")
        sorted_letters.extend(sorted([k for k in brands_by_letter.keys() if k != "other"]))

        brands_html = self._render_brands_html(brands_by_letter, sorted_letters)

        return http.request.render(
            "mapmedical_website_sale_brand.brands_page",
            {
                "brands_html": brands_html,
                "sorted_letters": sorted_letters,
                # Backward compat: DB template may still use QWeb iteration
                # until module is updated with --update.
                "brands_by_letter": brands_by_letter,
            },
        )

    @staticmethod
    def _render_brands_html(brands_by_letter, sorted_letters):
        """Build /brands page HTML in Python instead of QWeb.

        With ~3600 brands the original QWeb template performed thousands of
        t-call iterations, resulting in 550-650ms render time.  Building
        the same markup in Python and passing it via ``t-out`` reduces
        render time to ~100ms while producing identical visual output.
        """

        def _esc(text):
            return str(Markup.escape(text)) if text else ""

        parts = []
        for letter in sorted_letters:
            brands_list = brands_by_letter[letter]
            anchor = f"table_of_content_heading_1_{letter}"
            display = "#" if letter == "other" else _esc(letter)
            mid = (len(brands_list) + 1) // 2

            parts.append(f'<h2 id="{_esc(anchor)}" data-anchor="true">{display}</h2><div>')

            # Desktop: two columns
            parts.append('<div class="row d-none d-sm-flex"><div class="col-6">')
            for b in brands_list[:mid]:
                parts.append(
                    f'<p class="mb-0"><a href="/brand/{_esc(b.url)}" class="text-decoration-none">{_esc(b.name)}</a></p>'
                )
            parts.append('</div><div class="col-6">')
            for b in brands_list[mid:]:
                parts.append(
                    f'<p class="mb-0"><a href="/brand/{_esc(b.url)}" class="text-decoration-none">{_esc(b.name)}</a></p>'
                )
            parts.append("</div></div>")

            # Mobile: single column
            parts.append('<div class="d-block d-sm-none brands-columns-mobile">')
            for b in brands_list:
                parts.append(
                    f'<p class="mb-0 brand-item"><a href="/brand/{_esc(b.url)}" class="text-decoration-none">{_esc(b.name)}</a></p>'
                )
            parts.append("</div></div>")

        return Markup("".join(parts))

    def _get_brands_from_request(self):
        """Extract and validate brand IDs from request parameters."""
        return request.env["product.template"].get_brands_from_request()

    def _get_additional_extra_shop_values(self, values, **post):
        """Add brand-related values to the shop template context."""
        values = super()._get_additional_extra_shop_values(values, **post)

        brands_limit = int(
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mapmedical_website_sale_brand.brands_widget_limit", DEFAULT_BRANDS_WIDGET_LIMIT)
        )

        published_brands = request.env["product.manufacturer"].get_published_brands(limit=brands_limit)

        selected_brand_ids = self._get_brands_from_request()

        # Get brands that are selected but not in the widget (temporary display)
        temp_brands = request.env["product.manufacturer"].sudo()
        if selected_brand_ids:
            temp_brands = (
                request.env["product.manufacturer"]
                .sudo()
                .search([("id", "in", selected_brand_ids), ("id", "not in", published_brands.ids)])
            )

        values.update(
            {
                "published_brands": published_brands,
                "selected_brand_ids": selected_brand_ids,
                "temp_brands": temp_brands,
                "brands_widget_enabled": True,
            }
        )
        return values

    def _get_shop_domain(self, search, category, attrib_values, search_in_description=True, brands=None):
        """Extend the shop domain to include brand filtering."""
        domain = super()._get_shop_domain(search, category, attrib_values, search_in_description)

        if brands is None:
            brands = self._get_brands_from_request()
        if brands:
            brand_domain = [("manufacturer_id", "in", brands)]
            domain = expression.AND([domain, brand_domain])
        return domain

    def _shop_lookup_products(self, attrib_set, options, post, search, website):
        """Override to include brand filtering in product lookup."""
        # Get brands from URL parameters or from /brand/<slug> route
        brand_ids = self._get_brands_from_request()
        if brand_ids:
            options["brands"] = brand_ids
            post["brands"] = [str(b) for b in brand_ids]
        return super()._shop_lookup_products(attrib_set, options, post, search, website)

    def _get_search_options(
        self,
        category=None,
        attrib_values=None,
        tags=None,
        min_price=0.0,
        max_price=0.0,
        conversion_rate=1,
        brands=None,
        **post,
    ):
        """Extend search options to include brands."""
        options = super()._get_search_options(
            category=category,
            attrib_values=attrib_values,
            tags=tags,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            **post,
        )
        if brands is None:
            brands = self._get_brands_from_request()

        if brands:
            options["brands"] = brands
        return options

    def _shop_get_query_url_kwargs(self, category, search, min_price, max_price, attrib=None, order=None, **post):
        """Override to include brands in URL parameters."""
        kwargs = super()._shop_get_query_url_kwargs(
            category, search, min_price, max_price, attrib=attrib, order=order, **post
        )
        # Add brands to URL parameters
        brands = request.httprequest.args.getlist("brands")
        if brands:
            kwargs["brands"] = brands
        return kwargs

    @staticmethod
    def _should_show_brand_description(brand_ids, category):
        """
        Check if brand description should be displayed.

        Brand description is shown only when:
        - Exactly one brand is selected
        - No category is selected

        :param brand_ids: List of selected brand IDs
        :param category: Selected category (if any)
        :return: Tuple (should_show, brand_recordset)
        """
        brand = request.env["product.manufacturer"].sudo()
        if len(brand_ids) == 1 and not category:
            brand = request.env["product.manufacturer"].sudo().browse(brand_ids[0])
            if brand.exists():
                return True, brand
        return False, brand

    @http.route(["/brands/mega-menu"], type="http", auth="public", website=True, sitemap=False)
    def brands_mega_menu(self):
        """Return HTML content for brands mega menu."""
        mega_menu_data = request.env["product.template"].get_brands_mega_menu_data()
        return request.render(
            "mapmedical_website_sale_brand.brands_mega_menu_content",
            {
                "brand_columns": mega_menu_data["columns"],
                "total_brands": mega_menu_data["total_brands"],
                "max_column_size": mega_menu_data["max_column_size"],
                "brands_per_column": mega_menu_data["brands_per_column"],
            },
        )

    def _get_canonical_url(self, product, **kwargs):
        return None

    @http.route(
        [
            "/shop",
            "/shop/page/<int:page>",
            '/brand/<model("product.manufacturer"):brand>',
            "/brand/<string:custom_slug>",
            "/brand/<string:custom_slug>/page/<int:page>",
            '/<model("product.public.category"):category>',
            '/<model("product.public.category"):category>/page/<int:page>',
            "/<string:categ_string_slug>/<string:categ_product_slug>/page/<int:page>",
            "/<string:categ_string_slug>/<string:categ_product_slug>",
            "/<string:categ_string_slug>/<string:categ_parent_string_slug>/<string:categ_product_slug>/page/<int:page>",
            "/<string:categ_string_slug>/<string:categ_parent_string_slug>/<string:categ_product_slug>",
            "/<string:categ_top_string_slug>/<string:categ_parent_string_slug>/<string:categ_string_slug>/<string:categ_product_slug>",
        ],
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def shop(
        self,
        page=0,
        product=None,
        category=None,
        brand=None,
        custom_slug=None,
        categ_string_slug=None,
        parent_categ_slug=None,
        categ_parent_string_slug=None,
        categ_product_slug=None,
        search="",
        min_price=0.0,
        max_price=0.0,
        ppg=False,
        **post,
    ):
        # Itransition changes start
        if not isinstance(category, str) and category and not config["test_enable"]:
            categ_url = f"/{category.custom_url}-{str(category.id)}"
            if slug(category) not in request.httprequest.path:
                return request.redirect(categ_url, code=301)
        if categ_product_slug:
            name, record_id = unslug(categ_product_slug)
            product_slug = (
                request.env["product.template"]
                .sudo()
                .search(
                    [
                        ("id", "=", record_id),
                        ("website_slug", "ilike", categ_product_slug),
                    ],
                    limit=1,
                )
            )
            if product_slug.exists():
                if product_slug.website_url != request.httprequest.path:
                    return request.redirect(product_slug.website_url, code=301)
                product = product_slug

            # Try ID-based category lookup first (for slugs like "category-name-123")
            if record_id:
                category_slug = request.env["product.public.category"].sudo().browse(record_id)
                if category_slug.exists():
                    category = category_slug
            # Fallback: resolve category by custom_url (for slugs without numeric ID)
            if not category and categ_string_slug:
                custom_url = f"{categ_string_slug}/{categ_product_slug}"
                category = (
                    request.env["product.public.category"].sudo().search([("custom_url", "=", custom_url)], limit=1)
                )
            if category and not config["test_enable"]:
                categ_url = f"/{category.custom_url}-{str(category.id)}"
                if categ_url not in request.httprequest.path:
                    return request.redirect(categ_url, code=301)
            if not category and not product and categ_product_slug:
                return request.redirect("/shop", code=301)
            if not category and not product:
                # Try categ_product_slug alone as custom_url
                category = (
                    request.env["product.public.category"]
                    .sudo()
                    .search([("custom_url", "=", categ_product_slug)], limit=1)
                )
        # For product routes (/<parent>/<child>/<product>), resolve category
        # from URL path segments when not already set by categ_product_slug handler
        if product and not category and categ_string_slug:
            categ_parent = post.get("categ_parent_string_slug", "")
            categ_top = post.get("categ_top_string_slug", "")
            # Build custom_url from path segments
            parts = [p for p in [categ_top, categ_parent, categ_string_slug] if p]
            custom_url = "/".join(parts)
            category = request.env["product.public.category"].sudo().search([("custom_url", "=", custom_url)], limit=1)
        if product:
            request.update_context(
                main_object=product,
                seo_title=product.website_meta_title or product.name,
                default_title=product.website_meta_title or product.name,
                seo_description=product.website_meta_description,
                seo_object=product,
                can_optimize_seo=True,
                is_product=True,
                website_meta_title=product.website_meta_title or product.name,
                website_meta_description=product.website_meta_description,
                title=product.website_meta_title or product.name,
                description=product.website_meta_description,
            )

            # 2️⃣ Also set the request meta fields (some themes read this)
            request.website_meta_title = product.website_meta_title or product.name
            request.website_meta_description = product.website_meta_description
            return request.render(
                "website_sale.product", self._prepare_product_values(product, category, search, **post)
            )

        add_qty = int(post.get("add_qty", 1))
        try:
            min_price = float(min_price)
        except ValueError:
            min_price = 0
        try:
            max_price = float(max_price)
        except ValueError:
            max_price = 0
        show_description = False
        selected_brand = False
        # Resolve brand from custom_slug param or from URL path fallback
        # (routing may deliver /brand/<slug> via the generic /<str>/<str> rule
        # instead of the /brand/<string:custom_slug> rule).
        if not brand and not custom_slug:
            path = request.httprequest.path
            if path.startswith("/brand/"):
                custom_slug = path[len("/brand/") :]
        if not brand and custom_slug:
            brand = request.env["product.manufacturer"].sudo().search([("website_url", "=", custom_slug)], limit=1)
            if not brand:
                raise NotFound()
        if not brand:
            brand_ids = self._get_brands_from_request()
            if brand_ids:
                post["brands"] = [str(b) for b in brand_ids]
            show_description, selected_brand = self._should_show_brand_description(brand_ids, category)

        Category = request.env["product.public.category"]
        if category:
            category = Category.search([("id", "=", int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()
        else:
            category = Category
        # Itransition changes end
        website = request.env["website"].get_current_website()
        website_domain = website.website_domain()
        if ppg:
            try:
                ppg = int(ppg)
                post["ppg"] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = website.shop_ppg or 20

        ppr = website.shop_ppr or 4

        request_args = request.httprequest.args
        attrib_list = request_args.getlist("attrib")
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}
        if attrib_list:
            post["attrib"] = attrib_list

        filter_by_tags_enabled = website.is_view_active("website_sale.filter_products_tags")
        if filter_by_tags_enabled:
            tags = request_args.getlist("tags")
            # Allow only numeric tag values to avoid internal error.
            if tags and all(tag.isnumeric() for tag in tags):
                post["tags"] = tags
                tags = {int(tag) for tag in tags}
            else:
                post["tags"] = None
                tags = {}

        keep = QueryURL(
            "/", **self._shop_get_query_url_kwargs(category and int(category), search, min_price, max_price, **post)
        )

        now = datetime.timestamp(datetime.now())
        pricelist = website.pricelist_id
        if "website_sale_pricelist_time" in request.session:
            # Check if we need to refresh the cached pricelist
            pricelist_save_time = request.session["website_sale_pricelist_time"]
            if pricelist_save_time < now - 60 * 60:
                request.session.pop("website_sale_current_pl", None)
                website.invalidate_recordset(["pricelist_id"])
                pricelist = website.pricelist_id
                request.session["website_sale_pricelist_time"] = now
                request.session["website_sale_current_pl"] = pricelist.id
        else:
            request.session["website_sale_pricelist_time"] = now
            request.session["website_sale_current_pl"] = pricelist.id

        filter_by_price_enabled = website.is_view_active("website_sale.filter_products_price")
        if filter_by_price_enabled:
            company_currency = website.company_id.sudo().currency_id
            conversion_rate = request.env["res.currency"]._get_conversion_rate(
                company_currency, website.currency_id, request.website.company_id, fields.Date.today()
            )
        else:
            conversion_rate = 1

        url = "/shop"
        if search:
            post["search"] = search

        options = self._get_search_options(
            category=category,
            attrib_values=attrib_values,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            display_currency=website.currency_id,
            **post,
        )
        brand_ids = self._get_brands_from_request()
        # Fast path: when no search/filters are active, use search_count() + search(limit/offset)
        # instead of _shop_lookup_products() which loads ALL product IDs into memory (315K+).
        _fast_path = not search and not attrib_set and not min_price and not max_price and not post.get("tags")
        if _fast_path:
            Product = request.env["product.template"].with_context(bin_size=True)
            domain = self._get_shop_domain(search, category, attrib_values)
            if brand:
                domain = expression.AND([domain, [("manufacturer_id", "=", brand.id)]])
            elif brand_ids:
                domain = expression.AND([domain, [("manufacturer_id", "in", brand_ids)]])
            order = self._get_search_order(post)
            product_count = Product.search_count(domain)
            _offset = max(0, page - 1) * ppg if page else 0
            search_product = Product.search(domain, limit=ppg, offset=_offset, order=order)
            fuzzy_search_term = None
        else:
            fuzzy_search_term, product_count, search_product = self._shop_lookup_products(
                attrib_set, options, post, search, website
            )

        filter_by_price_enabled = website.is_view_active("website_sale.filter_products_price")
        if filter_by_price_enabled:
            # Reuse the domain already computed for the fast path to avoid
            # a second identical _get_shop_domain() call.
            if _fast_path:
                price_domain = domain
            else:
                Product = request.env["product.template"].with_context(bin_size=True)
                price_domain = self._get_shop_domain(search, category, attrib_values)
                if brand:
                    price_domain = expression.AND([price_domain, [("manufacturer_id", "=", brand.id)]])

            # This is ~4 times more efficient than a search for the cheapest and most expensive products
            query = Product._where_calc(price_domain)
            Product._apply_ir_rules(query, "read")
            from_clause, where_clause, where_params = query.get_sql()
            query = f"""
                SELECT COALESCE(MIN(list_price), 0) * %s, COALESCE(MAX(list_price), 0) * %s
                FROM {from_clause}
                WHERE {where_clause}
            """
            request.env.cr.execute(query, (conversion_rate, conversion_rate) + tuple(where_params))
            available_min_price, available_max_price = request.env.cr.fetchone()

            if min_price or max_price:
                # The if/else condition in the min_price / max_price value assignment
                # tackles the case where we switch to a list of products with different
                # available min / max prices than the ones set in the previous page.
                # In order to have logical results and not yield empty product lists, the
                # price filter is set to their respective available prices when the specified
                # min exceeds the max, and / or the specified max is lower than the available min.
                if min_price:
                    min_price = min_price if min_price <= available_max_price else available_min_price
                    post["min_price"] = min_price
                if max_price:
                    max_price = max_price if max_price >= available_min_price else available_max_price
                    post["max_price"] = max_price

        ProductTag = request.env["product.tag"]
        if filter_by_tags_enabled and search_product:
            all_tags = ProductTag.search(
                expression.AND(
                    [[("product_ids.is_published", "=", True), ("visible_on_ecommerce", "=", True)], website_domain]
                )
            )
        else:
            all_tags = ProductTag

        categs_domain = [("parent_id", "=", False)] + website_domain
        if search:
            search_categories = Category.search(
                [("product_tmpl_ids", "in", search_product.ids)] + website_domain
            ).parents_and_self
            categs_domain.append(("id", "in", search_categories.ids))
        else:
            search_categories = Category
        categs = lazy(lambda: Category.search(categs_domain))

        # Pre-render category sidebar HTML in Python (replaces ~780 recursive
        # QWeb t-calls for 193 categories × 2 sidebars).
        _prerender_cats = _fast_path and not search and not brand and not category
        if _prerender_cats:
            all_categs = Category.search(website_domain, order="sequence, name, id")
            categories_main_html = _prerender_categories_html(all_categs, category, brand, keep)
            categories_offcanvas_html = _prerender_categories_html(
                all_categs, category, brand, keep, radio_prefix="offcanvas_"
            )

        if category:
            url = f"/{category.custom_url}-{str(category.id)}"

        pager = website.pager(url=url, total=product_count, page=page, step=ppg, scope=5, url_args=post)
        offset = pager["offset"]
        if _fast_path:
            products = search_product
        else:
            products = search_product[offset : offset + ppg]

        ProductAttribute = request.env["product.attribute"]
        if products:
            if not search and not category and not attrib_set and not brand_ids and not brand:
                # No filters: show all visible attributes without passing 310K+ IDs
                attributes = lazy(lambda: ProductAttribute.search([("visibility", "=", "visible")]))
            else:
                attributes = lazy(
                    lambda: ProductAttribute.search(
                        [
                            ("product_tmpl_ids", "in", search_product.ids),
                            ("visibility", "=", "visible"),
                        ]
                    )
                )
        else:
            attributes = lazy(lambda: ProductAttribute.browse(attributes_ids))

        layout_mode = request.session.get("website_sale_shop_layout_mode")
        if not layout_mode:
            if website.viewref("website_sale.products_list_view").active:
                layout_mode = "list"
            else:
                layout_mode = "grid"
            request.session["website_sale_shop_layout_mode"] = layout_mode

        # Try to fetch geoip based fpos or fallback on partner one
        fiscal_position_sudo = website.fiscal_position_id.sudo()
        products_prices = lazy(lambda: products._get_sales_prices(pricelist, fiscal_position_sudo))

        values = {
            "search": fuzzy_search_term or search,
            "original_search": fuzzy_search_term and search,
            "order": post.get("order", ""),
            "category": category,
            "attrib_values": attrib_values,
            "attrib_set": attrib_set,
            "pager": pager,
            "pricelist": pricelist,
            "fiscal_position": fiscal_position_sudo,
            "add_qty": add_qty,
            "products": products,
            "search_product": search_product,
            "search_count": product_count,  # common for all searchbox
            "bins": lazy(lambda: TableCompute().process(products, ppg, ppr)),
            "ppg": ppg,
            "ppr": ppr,
            "categories": categs,
            "categories_main_html": categories_main_html if _prerender_cats else None,
            "categories_offcanvas_html": categories_offcanvas_html if _prerender_cats else None,
            "attributes": attributes,
            "keep": keep,
            "search_categories_ids": search_categories.ids,
            "layout_mode": layout_mode,
            "products_prices": products_prices,
            "get_product_prices": lambda product: lazy(lambda: products_prices[product.id]),
            "float_round": tools.float_round,
        }
        # Itransition changes start
        if not brand:
            if not post.get("order") or post.get("order") == "website_sequence asc":
                categ_sequence = (
                    request.env["product.brand.category.sequence"]
                    .sudo()
                    .search([("public_categ_id", "=", category.id)])
                )
                if categ_sequence:
                    sequence_products = categ_sequence.mapped("product_tmpl_id")
                    common = sequence_products & products
                    remaining = products - common
                    prods = common | remaining
                    values["products"] = prods
                    values["bins"] = lazy(lambda: TableCompute().process(prods, ppg, ppr))

        else:

            fiscal_position_sudo = website.fiscal_position_id.sudo()

            # Show only categories that directly contain products of this
            # brand — flat list, no parent expansion.
            brand_categs = Category.search([("product_tmpl_ids.manufacturer_id", "=", brand.id)] + website_domain)
            # Pass only top-level brand categories: those whose parent is
            # NOT itself in brand_categs.  Children that are also in
            # brand_categs will appear via the recursive template filtered
            # by search_categories_ids.
            brand_categ_ids = set(brand_categs.ids)
            top_brand_categs = brand_categs.filtered(lambda c: not c.parent_id or c.parent_id.id not in brand_categ_ids)
            values["categories"] = top_brand_categs
            # Tell QWeb recursive template to only show children that
            # belong to this brand (prevents expanding all subcategories).
            values["search_categories_ids"] = brand_categs.ids

            url = "/brand/%s" % custom_slug
            ppg = 20
            product_domain = self._get_shop_domain(search, category, attrib_values, brands=[brand.id])
            if category:
                post["category"] = category.id

            Product = request.env["product.template"].with_context(bin_size=True)
            order = self._get_search_order(post)
            products = Product.search(product_domain, order=order)

            # Apply price filter within the brand product set
            if filter_by_price_enabled and (min_price or max_price):
                brand_prices = products._get_sales_prices(pricelist, fiscal_position_sudo)
                filtered_ids = []
                for p in products:
                    price = brand_prices[p.id]["price_reduce"]
                    if min_price and price < min_price:
                        continue
                    if max_price and price > max_price:
                        continue
                    filtered_ids.append(p.id)
                products = Product.browse(filtered_ids)

            if not post.get("order") or post.get("order") == "website_sequence asc":
                brand_sequence = (
                    request.env["product.brand.category.sequence"].sudo().search([("manufacturer_id", "=", brand.id)])
                )
                sequence_products = brand_sequence.mapped("product_tmpl_id")

                common = sequence_products & products
                remaining = products - common
                products = common | remaining
            if min_price:
                post["min_price"] = min_price
            if max_price:
                post["max_price"] = max_price
            pager = website.pager(url=url, total=len(products), page=page, step=ppg, scope=5, url_args=post)
            products_prices = lazy(lambda: products._get_sales_prices(pricelist, fiscal_position_sudo))
            offset = pager["offset"]
            products = products[offset : offset + ppg]
            values["products"] = products
            values["bins"] = lazy(lambda: TableCompute().process(products, ppg, ppr))
            values["pager"] = pager
            values["page"] = page
            values["brand"] = brand
            values["category_header"] = ""
            # values["seo_text"] = ""
            values["seo_title"] = brand.seo_title
            values["seo_description"] = brand.seo_description
            values["website_meta_description"] = brand.seo_description
            values["title"] = brand.seo_title
            values["get_product_prices"] = lambda product: lazy(lambda: products_prices[product.id])
            request.update_context(
                main_object=brand,
                seo_title=brand.seo_title or brand.name,
                default_title=brand.seo_title or brand.name,
                seo_description=brand.seo_title,
                seo_object=brand,
                can_optimize_seo=True,
                website_meta_title=brand.seo_title or brand.name,
                website_meta_description=brand.seo_description,
                title=brand.seo_title,
                description=brand.seo_description,
            )

            # 2️⃣ Also set the request meta fields (some themes read this)
            request.website_meta_title = brand.seo_title or brand.name
            request.website_meta_description = brand.seo_description
        if filter_by_price_enabled:
            values["min_price"] = min_price or available_min_price
            values["max_price"] = max_price or available_max_price
            values["available_min_price"] = tools.float_round(available_min_price, 2)
            values["available_max_price"] = tools.float_round(available_max_price, 2)
        if filter_by_tags_enabled:
            values.update({"all_tags": all_tags, "tags": tags})
        if category:
            values["main_object"] = category
        if brand:
            values["brand"] = brand
        values.update(self._get_additional_extra_shop_values(values, **post))
        # Itransition changes end
        return request.render("website_sale.products", values)

    @http.route(['/shop/<model("product.template"):product>'], type="http", auth="public", website=True, sitemap=True)
    def product(self, product, category="", search="", **kwargs):
        if not config["test_enable"]:
            if len(product.public_categ_ids) > 0:
                return request.redirect(product.website_url, code=301)
        return request.render("website_sale.product", self._prepare_product_values(product, category, search, **kwargs))
