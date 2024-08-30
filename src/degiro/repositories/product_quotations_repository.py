import json

from django.db import connection

from degiro.utils.db_utils import dictfetchall


class ProductQuotationsRepository:
    def get_product_quotations(self, product_id: int) -> dict:
        """Gets the list of product ids from the DB.

        ### Returns
            list: list of product ids
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT quotations FROM degiro_productquotation WHERE id = %s
                """,
                [product_id],
            )
            results = dictfetchall(cursor)[0]["quotations"]

        return json.loads(results)

    def get_product_price(self, product_id: int) -> float:
        quotations = self.get_product_quotations(product_id)

        last_quotation = list(quotations.keys())[-1]

        return quotations[last_quotation]
