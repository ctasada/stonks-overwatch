
from django.db import connection

from degiro.utils.db_utils import dictfetchall


class ProductInfoRepository:
    def get_products_info_raw(self, ids) -> dict:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT *
                FROM degiro_productinfo
                WHERE id IN ({", ".join(map(str, ids))})
                """
            )
            rows = dictfetchall(cursor)

        # Convert the list of dictionaries into a dictionary indexed by 'productId'
        result_map = {row['id']: row for row in rows}
        return result_map
