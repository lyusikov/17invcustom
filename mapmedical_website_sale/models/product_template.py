from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools import escape_psql

THUMBNAIL_PATH = "/product/static/img/placeholder_thumbnail.png"


class ProductTemplate(models.Model):
    _inherit = "product.template"

    raw_name = fields.Char(compute="_compute_raw_name", store=True)

    @api.depends("mfr_product_code", "manufacturer_id.name")
    def _compute_raw_name(self):
        for rec in self:
            if rec.manufacturer_id.name and rec.mfr_product_code:
                raw_name = f"{rec.manufacturer_id.name} {rec.mfr_product_code}"
            else:
                raw_name = rec.manufacturer_id.name or rec.mfr_product_code or ""
            rec.raw_name = raw_name

    def _website_show_quick_add(self):
        self.ensure_one()
        if self.env.user.has_group("base.group_public"):
            return False
        return super()._website_show_quick_add()

    def _is_add_to_cart_possible(self, parent_combination=None):
        self.ensure_one()
        if self.env.user.has_group("base.group_public"):
            return False
        return super()._is_add_to_cart_possible(parent_combination)

    def _search_render_results(self, fetch_fields, mapping, icon, limit):
        """
        Replace OOTB image with product url_image field content
        """
        res = super()._search_render_results(fetch_fields, mapping, icon, limit)
        lead_time_values = dict(self._fields["customer_lead_time"].selection)
        for item in res:
            product = self.browse(item["id"])
            if "image_url" in mapping:
                item["image_url"] = product.url_image or THUMBNAIL_PATH
            item["customer_lead_time"] = lead_time_values.get(product.customer_lead_time)
        return res

    @api.model
    def _search_get_detail(self, website, order, options):
        """
        Add page number(in case when all results page with paginator) into getting search details
        and change searchable fields and mapping options
        """
        res = super()._search_get_detail(website, order, options)
        res["mapping"]["customer_lead_time"] = {
            "match": True,
            "name": "customer_lead_time",
            "type": "text",
        }
        res["search_fields"] = ["name", "mfr_product_code", "description_sale", "raw_name", "unique_reference"]
        if "page" in options:
            res["page"] = options["page"]
        return res

    @api.model
    def _search_build_domain(self, domain_list, search, fields, extra=None):
        """
        Override method to get prioritized domains for searching
        """
        base_domain = domain_list.copy()
        base_subdomain = [extra(self.env, search)] if extra else []

        if not fields:
            return (expression.AND([*base_domain, *base_subdomain]), [], [])

        first_priority_domain = base_subdomain.copy()
        first_priority_domain.append([(fields[0], "=ilike", f"{escape_psql(search)}%")])

        second_priority_domain = base_subdomain.copy()
        second_priority_domain.append([(fields[0], "ilike", f"{escape_psql(search)}")])

        third_priority_domain = base_subdomain.copy()
        third_priority_domain.extend([[(field, "ilike", f"{escape_psql(search)}")] for field in fields[1:]])

        return (
            expression.AND([*base_domain, expression.OR(first_priority_domain)]),
            expression.AND([*base_domain, expression.OR(second_priority_domain)]),
            expression.AND([*base_domain, expression.OR(third_priority_domain)]),
        )

    @api.model
    def _search_fetch(self, search_detail, search, limit, order):
        """
        Override method to get prioritized result of search.

        When *search* is empty the 3-priority-domain logic is skipped because
        it generates ``unaccent(name ILIKE '%')`` on every row — three times —
        which is extremely expensive on 310K+ products (30 s on staging).
        """
        fields = search_detail["search_fields"]
        base_domain = search_detail["base_domain"]
        # Itransition changes start
        page = search_detail.get("page", 0)
        order = search_detail.get("order", order)
        model = self.sudo() if search_detail.get("requires_sudo") else self

        if not search:
            # Fast path: no search term → single query without unaccent overhead
            domain = expression.AND(base_domain)
            results = model.search(domain, order=order)
            count = len(results)
        else:
            domain_1, domain_2, domain_3 = self._search_build_domain(
                base_domain, search, fields, search_detail.get("search_extra")
            )
            results = model.search(domain_1, order=order)
            if fields:
                results |= model.search(domain_2, order=order)
                results |= model.search(domain_3, order=order)
            count = len(results)
        # if page was provided then use it to take part of result
        if page:
            res = results[(page - 1) * 50 : 50 * page]
        else:
            res = results[:limit]
        return res, count
        # Itransition changes end
