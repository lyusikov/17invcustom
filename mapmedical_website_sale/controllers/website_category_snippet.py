from odoo import http
from odoo.http import request


class WebsiteCategorySnippet(http.Controller):
    @http.route("/shop/get_category", type="json", auth="public")
    def get_website_category(self, **kw):
        """Endpoint to get Public Categories."""
        categories = request.env["product.public.category"].sudo().search([("parent_id", "=", False)], order="name")
        data = self._get_website_category_json(categories)
        return data

    def _get_website_category_json(self, categories):
        data_list = [
            {
                "id": str(categ.id),
                "name": categ.name,
                "child_ids": [{"id": child.id, "name": child.name} for child in categ.child_id.sorted("name")],
            }
            for categ in categories
        ]
        data = {"data": data_list}
        return data
