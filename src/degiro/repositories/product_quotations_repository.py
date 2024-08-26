
import json
from django.db import connection

from degiro.utils.db_utils import dictfetchall


class ProductQuotationsRepository:
    def get_product_quotations(self, productId: int) -> dict:
        """
        Gets the list of product ids from the DB.

        ### Returns
            list: list of product ids
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT quotations FROM degiro_productquotation WHERE id = %s
                """,
                [productId],
            )
            results = dictfetchall(cursor)[0]["quotations"]

        return json.loads(results)
