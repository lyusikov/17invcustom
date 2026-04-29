from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return

    cr.execute("ALTER TABLE product_template ADD raw_name CHARACTER VARYING")
    cr.execute(
        """
            UPDATE product_template pt
            SET raw_name = CONCAT(pm.name, ' ', pt.mfr_product_code)
            FROM product_template pt2
            JOIN product_manufacturer pm ON pm.id = pt2.manufacturer_id
            WHERE pt2.id = pt.id
        """
    )
