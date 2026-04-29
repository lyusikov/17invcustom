from odoo.http import request, route
from odoo import _
from odoo.addons.mapmedical_website_sale_brand.controllers.main import WebsiteBrand


class WebSiteSaleRybakavun(WebsiteBrand):

    @route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>'
        + '/page/<int:page>',
    ], type='http', methods=['GET', 'POST'], auth="public", website=True)
    def shop(self, page=0, category=None, search='',
             min_price=0.0, max_price=0.0, ppg=False, **post):
        res = super(WebSiteSaleRybakavun, self).shop(
            page=page,
            category=category,
            search=search,
            min_price=min_price,
            max_price=max_price,
            ppg=ppg,
            **post
        )
        if res.qcontext.get("main_object") and res.qcontext.get("main_object")._name == "product.template":
            return res
        page_prefix = ''
        if page:
            page_prefix = _('Page №') + ' ' + str(page)
        category=res.qcontext.get("category")
        # Category = request.env["product.public.category"]
        # if category:
        #     category = Category.search([("id", "=", int(category))], limit=1)
        #     if not category or not category.can_access_from_current_website():
        #         raise NotFound()
        # elif res.qcontext.get("category"):
        #     category=res.qcontext.get("category")
        # else:
        #     category = Category
        current_route = request.httprequest.path
        if current_route == '/shop' or current_route.startswith('/shop/page'):
            seo_record = request.env['seo.model'].search([
                ('apply_all_products_page', '=', True),
                '|',
                ('website_ids', '=', False),
                ('website_ids', 'in', request.website.id),
            ], limit=1)

            res.qcontext.update({
                'seo_title': page_prefix + ' '
                + (seo_record.seo_title or self.get_default_title(request)),
                'seo_description': page_prefix + ' '
                + (seo_record.seo_description or ''),
                'main_header': f"{page_prefix} {seo_record.seo_header or ''}",
                'seo_text': seo_record.seo_text
                if not page and seo_record.seo_text else ''})
            return res
        if not category:
            return res
        res.qcontext.update({
            'seo_title': page_prefix + ' '
            + (category.website_meta_title or self.get_default_title(request)),
            'seo_description': page_prefix + ' '
            + (category.website_meta_description or ''),
            'category_header': category.name,
        })

        criteria = request.env['ir.config_parameter']\
            .sudo()\
            .get_param('kw_seo_configuration.seo_criteria', default='category')
        seo_record_domain = []

        if criteria in ('category', 'both'):
            seo_record_domain.append(
                ('related_categories_ids', 'in', [category.id])
            )

        if criteria in ('attributes', 'both'):
            attrib_value_id = self.get_attr_value_id(
                request.httprequest.args.getlist('attrib')
            )
            seo_record_domain.append(
                ('attr_values_ids', 'in', [attrib_value_id])
            )
        seo_record = request\
            .env['seo.model']\
            .search(seo_record_domain, limit=1)
        if not seo_record:
            return res

        res.qcontext.update({
            'seo_title': f"{page_prefix} {seo_record.seo_title}",
            'seo_description': f"{page_prefix} {seo_record.seo_description}",
            'website_meta_description':seo_record.seo_description,
            'seo_text': seo_record.seo_text if not page else '',
            'category_header': f"{page_prefix} {seo_record.seo_header}"
                               if seo_record.seo_header else None,
        })
        
        return res

    def get_attr_value_id(self, attrib_list):
        attrib_values = [
            [int(x) for x in v.split("-")] for v in attrib_list if v
        ]

        return attrib_values[0][1] if len(attrib_values) else ''

    def get_default_title(self, request_obj):
        website_name = request_obj.env["website"].get_current_website().name
        return _("Shop | %s") % website_name
