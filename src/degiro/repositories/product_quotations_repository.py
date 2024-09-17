import json

from django.db import connection

from degiro.utils.db_utils import dictfetchall


class ProductQuotationsRepository:
    def get_product_quotations(self, product_id: int) -> dict:
        """Gets the quotations from the specified product_id from the DB.

        ### Returns
            List of quotations, or None if the product is not found
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT quotations FROM degiro_productquotation WHERE id = %s
                """,
                [product_id],
            )
            results = dictfetchall(cursor)

        if results:
            return json.loads(results[0]["quotations"])

        return None

    def get_product_price(self, product_id: int) -> float:
        """Gets the last quotation from the specified product_id from the DB.

        ### Returns
            Last quotation, or 0.0 if the product is not found
        """
        quotations = self.get_product_quotations(product_id)
        if quotations:
            last_quotation = list(quotations.keys())[-1]

            return quotations[last_quotation]

        return 0.0
